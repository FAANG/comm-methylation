#
# Copyright (C) 2016 INRA
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#----------------------------------------------------------------------
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

