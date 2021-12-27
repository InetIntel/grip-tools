#!/bin/bash
#SBATCH --job-name=grip-moas-2020
#SBATCH --output="logs/observatory-rerun-moas.%j.%N.out"
#SBATCH --error="logs/observatory-rerun-moas.%j.%N.err"
#SBATCH --partition=compute
#SBATCH -t 48:00:00
#SBATCH --mem=120G
#SBATCH --cpus-per-task=6
#SBATCH --nodes=1
#SBATCH --no-requeue            ### SLURM will requeue jobs if there is a node failure.
#SBATCH --export=ALL
#SBATCH -A TG-CIS200040          ### HIJACKS grant
#SBATCH --array=0-1            ### $SLURM_ARRAY_TASK_ID

TIME=`date +%Y-%m-%d-%H`
for i in `seq 0 23`; do
    TID=$(($i + $SLURM_ARRAY_TASK_ID*2))
    # run for a whole year, 4 tasks per month, total of 48 tasks
    python run.py -s 1577836800 -e 1609459200 -t moas -T 48 -i $TID  > "logs/$TIME-moas-$TID.out" 2>"logs/$TIME-moas-$TID.err" &
done
wait
