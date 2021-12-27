# Inference Scripts

## Rerunning Inference Engine

Script: [inference-runner.py](inference-runner.py)

Parameters:
- `type` (required): event type to rerun, must specify one
- `start_ts` (required): starting timestamp for events to re-inference
- `end_ts`: ending timestamp for events to re-inference, default to now
- `before_ts`: the timestamp that the events must be inserted before 
- `after_ts`: the timestamp that the events must be inserted after 
- `debug`: whether to running it in debug mode
- `processes`: number of parallel processes to rerun, default to 1, specify 0 to use all available cores
- `tr_worthy`: only re-inference traceroute-worthy events
- `must_tags`: only re-inference events with specified tags, separated by comma
- `must_not_tags`: never re-inference events with specified tags, separated by comma

