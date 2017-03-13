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

#Path to the directory where RRBS pipeline is installed (directory where this configuration file is located)
RRBS_HOME=/save/bdr-er5/RRBS-toolkit

#path to the directory where bismark is installed
BISMARK_HOME=/usr/local/bioinfo/src/Bismark/bismark_v0.14.3

#path to the directory where bowtie (v1) is installed
BOWTIE_HOME=/usr/local/bioinfo/src/bowtie/bowtie-0.12.9

#path to the trim_galore executable file
TRIMGALORE_EXECUTE=/usr/local/bioinfo/src/Trim_Galore/trim_galore_v0.4.0/trim_galore

#path to the cut_adapt executable file
CUTADAPT_EXECUTE=/usr/local/bioinfo/src/cutadapt/cutadapt-1.7.1/bin/cutadapt

#path to the samtools executable file
SAMTOOLS_EXECUTE=/usr/local/bioinfo/src/samtools/samtools-1.1/samtools

#path to the python (v2.7) executable file
PYTHON_EXECUTE=/usr/local/bioinfo/src/python/Python-2.7.2/bin/python

#path to the R executable file
R_EXECUTE=/usr/local/bioinfo/bin/R

export RRBS_HOME BISMARK_PIPELINE_HOME BISMARK_HOME BOWTIE_HOME TRIMGALORE_EXECUTE CUTADAPT_EXECUTE SAMTOOLS_EXECUTE PYTHON_EXECUTE R_EXECUTE
