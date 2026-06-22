from .utils import *
from .search import match_cat


def load_flare_catalog(filepath, time_col='center_time_abs'):
    """
    Load a flare catalog from an Excel file and convert the reference time
    column to MJD.

    Parameters
    ----------
    filepath : str
        Path to the xlsx file.
    time_col : str
        Name of the column containing ISO-format datetime strings.

    Returns
    -------
    flare_cat : astropy.Table
        Flare catalog with an added ``mjd`` column.
    """
    df = pd.read_excel(filepath)
    times = Time(df[time_col].tolist(), format='isot')
    df['mjd'] = times.mjd
    return Table.from_pandas(df)


def cross_match_flares(
    flare_cat,
    optical_cat,
    radius=3.0,
    dt_window=(-30, 30),
    flare_ra_col='ra',
    flare_dec_col='dec',
    flare_time_col='mjd',
    flare_name_col='name',
    opt_ra_col='o_ra',
    opt_dec_col='o_dec',
    opt_time_col='firstmjd',
    opt_name_col='oid',
    pipeline_label='Flare-Optical',
):
    """
    Cross-match a flare catalog with an optical transient catalog.

    Performs two-stage matching:
    1. Spatial: sky-coordinate match within *radius* arcminutes.
    2. Temporal: keep pairs whose ``dt = opt_mjd - flare_mjd`` falls inside
       ``dt_window``.

    Parameters
    ----------
    flare_cat : astropy.Table
        Flare catalog (must contain ra, dec, mjd, and name columns).
    optical_cat : astropy.Table
        Optical transient catalog (must contain o_ra, o_dec, firstmjd, oid).
    radius : float
        Search radius in arcminutes.
    dt_window : tuple of (float, float)
        (min_dt, max_dt) in days.  dt = optical_mjd - flare_mjd.
    flare_ra_col, flare_dec_col, flare_time_col, flare_name_col : str
        Column names in the flare catalog.
    opt_ra_col, opt_dec_col, opt_time_col, opt_name_col : str
        Column names in the optical catalog.
    pipeline_label : str
        Label written into the ``pipeline`` column of the result.

    Returns
    -------
    result : astropy.Table
        Matched pairs with columns:
        flare_name, oid, flare_ra, flare_dec, o_ra, o_dec,
        separation (arcsec), flare_mjd, firstmjd, dt, pipeline
    """
    if len(flare_cat) == 0 or len(optical_cat) == 0:
        return Table()

    flare_coords = SkyCoord(flare_cat[flare_ra_col], flare_cat[flare_dec_col], unit=u.deg)
    opt_coords = SkyCoord(optical_cat[opt_ra_col], optical_cat[opt_dec_col], unit=u.deg)

    source_matched_idx, cat_matched_idx, sep = match_cat(
        flare_coords, opt_coords, radius=radius * u.arcmin, seperation=True
    )

    if np.sum(source_matched_idx) == 0:
        return Table()

    flare_matched = flare_cat[source_matched_idx]
    opt_matched = optical_cat[cat_matched_idx]

    dt = opt_matched[opt_time_col] - flare_matched[flare_time_col]
    time_mask = (dt >= dt_window[0]) & (dt <= dt_window[1])

    if np.sum(time_mask) == 0:
        return Table()

    flare_matched = flare_matched[time_mask]
    opt_matched = opt_matched[time_mask]
    sep = sep[time_mask]
    dt = dt[time_mask]

    n = len(flare_matched)
    result = Table(
        {
            'flare_name': np.array(flare_matched[flare_name_col], dtype='U50'),
            'oid': np.array(opt_matched[opt_name_col], dtype='U50'),
            'flare_ra': np.array(flare_matched[flare_ra_col], dtype='f8'),
            'flare_dec': np.array(flare_matched[flare_dec_col], dtype='f8'),
            'o_ra': np.array(opt_matched[opt_ra_col], dtype='f8'),
            'o_dec': np.array(opt_matched[opt_dec_col], dtype='f8'),
            'separation (arcsec)': sep.arcsec,
            'flare_mjd': np.array(flare_matched[flare_time_col], dtype='f8'),
            'firstmjd': np.array(opt_matched[opt_time_col], dtype='f8'),
            'dt': np.array(dt, dtype='f8'),
            'pipeline': np.array([pipeline_label] * n, dtype='U30'),
        }
    )

    return result


def match_one_flare(
    flare,
    optical_cat,
    radius=3.0,
    dt_window=(-30, 30),
    flare_ra_col='ra',
    flare_dec_col='dec',
    flare_time_col='mjd',
    flare_name_col='name',
    opt_ra_col='o_ra',
    opt_dec_col='o_dec',
    opt_time_col='firstmjd',
    opt_name_col='oid',
    pipeline_label='Flare-Optical',
):
    """
    Cross-match a single flare against an optical transient catalog.

    Spatial matching is performed **first**: all optical transients within
    *radius* arcminutes of the flare are found.  Then ``dt`` is computed
    for each.  If *dt_window* is given, only matches falling inside it are
    returned; pass ``None`` to return all spatial matches regardless of time.

    Parameters
    ----------
    flare : astropy.Table.Row or dict
        A single flare with ra, dec, mjd, and name.
    optical_cat : astropy.Table
        Full optical transient catalog.
    radius : float
        Search radius in arcminutes.
    dt_window : tuple of (float, float) or None
        (min_dt, max_dt) in days.  dt = optical_mjd - flare_mjd.
        If None, all spatial matches are returned.
    pipeline_label : str
        Label written into the ``pipeline`` column of the result.

    Returns
    -------
    result : astropy.Table
        Matched pairs (same columns as ``cross_match_flares``), or an empty
        table if no spatial match is found.
    """
    flare_mjd = flare[flare_time_col]

    flare_coord = SkyCoord(flare[flare_ra_col], flare[flare_dec_col], unit=u.deg)
    opt_coords = SkyCoord(optical_cat[opt_ra_col], optical_cat[opt_dec_col], unit=u.deg)

    # ---- Step 1: spatial match — find ALL optical transients within radius ----
    seps = flare_coord.separation(opt_coords)
    spatial_mask = seps < radius * u.arcmin

    if np.sum(spatial_mask) == 0:
        return Table()

    matched_opt = optical_cat[spatial_mask]
    matched_seps = seps[spatial_mask]
    dt = matched_opt[opt_time_col] - flare_mjd

    # ---- Step 2: time filter (only if dt_window is set) ----
    if dt_window is not None:
        time_mask = (dt >= dt_window[0]) & (dt <= dt_window[1])
        if np.sum(time_mask) == 0:
            return Table()
        matched_opt = matched_opt[time_mask]
        matched_seps = matched_seps[time_mask]
        dt = dt[time_mask]

    n = len(matched_opt)
    result = Table(
        {
            'flare_name': np.full(n, str(flare[flare_name_col]), dtype='U50'),
            'oid': np.array(matched_opt[opt_name_col], dtype='U50'),
            'flare_ra': np.full(n, float(flare[flare_ra_col]), dtype='f8'),
            'flare_dec': np.full(n, float(flare[flare_dec_col]), dtype='f8'),
            'o_ra': np.array(matched_opt[opt_ra_col], dtype='f8'),
            'o_dec': np.array(matched_opt[opt_dec_col], dtype='f8'),
            'separation (arcsec)': matched_seps.arcsec,
            'flare_mjd': np.full(n, flare_mjd, dtype='f8'),
            'firstmjd': np.array(matched_opt[opt_time_col], dtype='f8'),
            'dt': np.array(dt, dtype='f8'),
            'pipeline': np.full(n, pipeline_label, dtype='U30'),
        }
    )

    return result
