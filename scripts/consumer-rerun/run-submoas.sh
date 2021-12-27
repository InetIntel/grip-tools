#!/bin/bash
#SBATCH --job-name=observatory-rerun-submoas
#SBATCH --output="logs/observatory-rerun-submoas.%j.%N.out"
#SBATCH --error="logs/observatory-rerun-submoas.%j.%N.err"
#SBATCH --partition=compute
#SBATCH -t 36:00:00
#SBATCH --mem=120G
#SBATCH --nodes=1
#SBATCH --cpus-per-task=12
#SBATCH --no-requeue            ### SLURM will requeue jobs if there is a node failure.
#SBATCH --export=ALL
#SBATCH -A TG-CIS200040          ### HIJACKS grant
#SBATCH --array=0-1            ### $SLURM_ARRAY_TASK_ID

TIME=`date +%Y-%m-%d-%H`
for i in `seq 0 1 2`; do
    TID=$(($i + $SLURM_ARRAY_TASK_ID*3))
    python run.py -s 1577836800 -e 1580515200 -t submoas -T 4 -i $TID > "logs/$TIME-submoas-$TID.out" 2>"logs/$TIME-submoas-$TID.err" &
done
wait

