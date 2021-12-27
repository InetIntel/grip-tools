#!/bin/bash
#SBATCH --job-name=observatory-rerun-edges
#SBATCH --output="logs/observatory-rerun-edges.%j.%N.out"
#SBATCH --error="logs/observatory-rerun-edges.%j.%N.err"
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
    python run.py -s 1577836800 -e 1580515200 -t edges -T 4 -i $TID  > "logs/$TIME-edges-$TID.out" 2>"logs/$TIME-edges-$TID.err" &
done
wait
