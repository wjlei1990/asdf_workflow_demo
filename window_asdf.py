import os
import json
import matplotlib
from copy import deepcopy
from pprint import pprint
import logging

from pyasdf import ASDFDataSet
from utils import load_json, load_yaml, safe_mkdir, write_json
import pyflex
from pytomo3d.window.io import get_json_content, WindowEncoder

# set pyflex logging level
pyflex.logger.setLevel(logging.INFO)


def parse_param_yaml(param):
    # reform the param from default
    default = param["default"]
    comp_settings = param["components"]
    results = {}
    for _comp, _settings in comp_settings.items():

        results[_comp] = deepcopy(default)
        if _settings is None:
            continue

        for k, v in _settings.items():
            results[_comp][k] = v

        for k in ["instrument_merge_flag", "write_window_with_phase"]:
            # key not in use
            results[_comp].pop(k, None)

    return results


def write_window_json(results, output_file, with_phase=False):
    window_all = {}
    for station, sta_win in results.items():
        if sta_win is None:
            continue
        window_all[station] = {}
        _window_comp = {}
        for trace_id, trace_win in sta_win.items():
            _window = [get_json_content(_i, with_phase=with_phase)
                       for _i in trace_win]
            _window_comp[trace_id] = _window
        window_all[station] = _window_comp

    with open(output_file, 'w') as fh:
        j = json.dumps(window_all, cls=WindowEncoder, sort_keys=True,
                       indent=2, separators=(',', ':'))
        try:
            fh.write(j)
        except TypeError:
            fh.write(j.encode())


def load_window_param_file(fn):
    values = load_yaml(fn)
    params = parse_param_yaml(values)
    return params


def select_windows_asdf(obs_ds, obs_tag, syn_ds, syn_tag, params):
    obs_stations = obs_ds.waveforms.list()
    print("Number of stations in observed: {}".format(len(obs_stations)))

    # earthquake event info -- QuakeML
    event = obs_ds.events[0]

    windows = {}

    for station_name in obs_stations:

        if station_name not in syn_ds.waveforms:
            # syn_ds does NOT have this stations, skip
            continue

        if obs_tag in obs_ds.waveforms[station_name]:
            obs_stream = obs_ds.waveforms[station_name][obs_tag]
        else:
            continue

        if syn_tag in syn_ds.waveforms[station_name]:
            syn_stream = syn_ds.waveforms[station_name][syn_tag]
        else:
            continue

        stationXML = obs_ds.waveforms[station_name]["StationXML"]

        print(f"\n===> Processing station group: {station_name}")
        _window = select_windows_stream(obs_stream, syn_stream, params, event, stationXML)
        windows[station_name] = _window

    return windows


def select_windows_stream(obs_stream, syn_stream, params, event, stationXML):
    """
    Select windows on a pair of obsd stream and syn stream
    """
    windows = {}
    for obs_tr in obs_stream:
        obs_trace_id = obs_tr.id
        _nw, _sta, _chan, _comp = obs_trace_id.split(".")
        syn_trace_id = "{}.{}.S3.MX{}".format(_nw, _sta, _comp[-1])
        syn_tr = syn_stream.select(id=syn_trace_id)

        if len(syn_tr) == 0:
            print(f"Not found trace id [{syn_trace_id}] in synt station group. Skip!")
            continue

        # component specific param
        if _comp not in params:
            print(f"Component not in param list [{obs_trace_id}]. Skip!")
            continue

        _param = params[_comp]
        _window = select_windows_trace(obs_tr, syn_tr[0], _param, event, stationXML)
        windows[obs_trace_id] = _window

    return windows


def select_windows_trace(obs_trace, syn_trace, params, event, stationXML):
    """
    Select windows on a pair of obsd trace and syn trace
    """
    config = pyflex.Config(**params)
    print("\n\n---- obs trace: ", obs_trace)
    print("---- syn trace: ", syn_trace)
    print("---- Event: ", event)
    print("---- StationXML: ", stationXML)

    ws = pyflex.WindowSelector(obs_trace, syn_trace, config, event=event, station=stationXML)
    windows = ws.select_windows()
    print(f"Number of windows selected: {len(windows)}")
    return windows


def main():
    eventname = "C200501011908A"
    period_band = "17_40"

    obs_tag = f"proc_obsd_{period_band}"
    # load observed asdf file
    obs_file = f"data/{eventname}.{obs_tag}.h5"
    print(f"obsd filename: {obs_file}")
    obs_ds = ASDFDataSet(obs_file, mpi=False, mode='r')
    print("obs asdf: ", obs_ds)

    syn_tag = f"proc_synt_{period_band}"
    syn_file = f"data/{eventname}.{syn_tag}.h5"
    # load synthetic asdf file
    syn_ds = ASDFDataSet(syn_file, mpi=False, mode='r')
    print("syn asdf: ", syn_ds)

    # load corresponding parameter file
    params = load_window_param_file(f"./params/CreateWindows/window.{period_band}#body_wave.param.yml")
    print("window selection config parameters:")
    pprint(params)

    # call window selection on obsd asdf and synt asdf
    windows = select_windows_asdf(obs_ds, obs_tag, syn_ds, syn_tag, params)
    print(windows)

    # prepare output directory
    outputdir = "data/window/"
    safe_mkdir(outputdir)
    outputfn = os.path.join(outputdir, f"{eventname}.{period_band}.json")
    print("Save window to file: {}".format(outputfn))
    write_window_json(windows, outputfn)


if __name__ == "__main__":
    main()
