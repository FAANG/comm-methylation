#
#----------------------------------------------------------------
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#----------------------------------------------------------------
#authors :
#---------
#	Piumi Francois (francois.piumi@inra.fr)		software conception and development (engineer in bioinformatics)
#	Jouneau Luc (luc.jouneau@inra.fr)		software conception and development (engineer in bioinformatics)
#	Gasselin Maxime (m.gasselin@hotmail.fr)		software user and data analysis (PhD student in Epigenetics)
#	Perrier Jean-Philippe (jp.perrier@hotmail.fr)	software user and data analysis (PhD student in Epigenetics)
#	Al Adhami Hala (hala_adhami@hotmail.com)	software user and data analysis (postdoctoral researcher in Epigenetics)
#	Jammes Helene (helene.jammes@inra.fr)		software user and data analysis (research group leader in Epigenetics)
#	Kiefer Helene (helene.kiefer@inra.fr)		software user and data analysis (principal invertigator in Epigenetics)
#

python get_venn.py \
        --set-file "../Differential_analysis/analysis_examples/out_methylKit/MethylKit - Condition A vs B - pvalue0.01 - with obvious DMCs.txt" \
        --set-file "../Differential_analysis/analysis_examples/out_methylSig/MethylSig - Condition A vs B - pvalue0.01 - with obvious DMCs.txt" \
        --set-name methylKit methylSig \
        --txt-output-file example_output/Venn_methylKit_methylSig.txt \
        --img-output-file example_output/Venn_methylKit_methylSig.jpg \
        --venn-title "methylKit vs methylSig results"  \
        --key-columns 1,2 \
        --keep-columns "Methyl diff" "Methylation state in Condition_A" 

