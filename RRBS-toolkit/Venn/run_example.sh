python get_venn.py \
        --set-file "../Differential_analysis/analysis_examples/out_methylKit/MethylKit - Condition A vs B - pvalue0.01 - with obvious DMCs.txt" \
        --set-file "../Differential_analysis/analysis_examples/out_methylSig/MethylSig - Condition A vs B - pvalue0.01 - with obvious DMCs.txt" \
        --set-name methylKit methylSig \
        --txt-output-file example_output/Venn_methylKit_methylSig.txt \
        --img-output-file example_output/Venn_methylKit_methylSig.jpg \
        --venn-title "methylKit vs methylSig results"  \
        --key-columns 1,2 \
        --keep-columns "Methyl diff" "Methylation state in Condition_A" 

