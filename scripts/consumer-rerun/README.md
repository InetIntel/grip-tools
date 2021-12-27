# Consumer Rerun

## Running Location

The scripts should be running on SDSC `Comet` or `Expanse`, and the storage space is on `oasis`.

## Example Slurm Script

``` bash
#!/bin/bash
#SBATCH --job-name=observatory-rerun-moas
#SBATCH --output="logs/observatory-rerun-moas.%j.%N.out"
#SBATCH --error="logs/observatory-rerun-moas.%j.%N.err"
#SBATCH --partition=compute
#SBATCH -t 48:00:00
#SBATCH --mem=120G
#SBATCH --cpus-per-task=6
#SBATCH --nodes=1
#SBATCH --no-requeue            ### SLURM will requeue jobs if there is a node failure.
#SBATCH --export=ALL
#SBATCH -A TG-NCR200002         ### HIJACKS grant
#SBATCH --array=0-1            ### $SLURM_ARRAY_TASK_ID

TIME=`date +%Y-%m-%d-%H`
for i in `seq 0 1`; do
    TID=$(($i + $SLURM_ARRAY_TASK_ID*2))
    python run.py -s 1577836800 -e 1580515200 -t moas -T 4 -i $TID  > "logs/$TIME-moas-$TID.out" 2>"logs/$TIME-moas-$TID.err" &
done
wait
```

- `--array=0-1`: we want to run two jobs
- `seq 0 1`: each job has two tasks
- `--mem=120G`: use 120G total per node across tasks
- `--cpus-per-task=6`: use 6 cpus per task

## Run Script

- `sbatch run-moas.sh`
- `scancel`: cancel job
- `sstat`: cancel job
- `sacct`: check running status
- `show_accounts`
