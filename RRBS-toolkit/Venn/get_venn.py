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

from string import *

import sys

import os
from os import getcwd
import re

from collections import OrderedDict

import argparse

import matplotlib as mpl

#Enable to produce image without X11 : has to be specified before import of pyplot
mpl.use('Agg')
from matplotlib import pyplot as plt
from matplotlib_venn import venn2, venn2_circles, venn2_unweighted
from matplotlib_venn import venn3, venn3_circles, venn3_unweighted

"""

Look for elements common to 2 or 3 sets

format fichier entree :

Chromosome	Start	End      Cov83   FreqC83 Cov82   FreqC82   Cov81   FreqC81 Cov80   FreqC80qvalue   Methyl diff
1		282752  282753   31      6       40      4         21      10      22      15              -44.0550278414674

element communs : recherche sur la position
 
Sortie : pour chaque position, indique si elle est commune ou pas entre les differents fichiers
donne aussi les valeurs de "Methyl diff" pour chaque position

exemple pour deux fichiers :
CpG position  |  Only in file_1 | Only in file_2 | Common in file_1 & file_2 | Methyl diff file_1 | Methyl diff file_2


"""
### FONCTIONS DE TRI

def numeric_compare(x, y):
	CpG1=re.split("[:-]",x)
	CpG2=re.split("[:-]",y)
	if (CpG1[0] == CpG2[0]):
		#Meme chromosome : on compare numeriquement les coordonnees
		return int(CpG1[1]) - int(CpG2[1])
	else:
		#Les chromosomes sont dfifferents : on les compare
		chr1_is_num=re.match("^[0-9]+$",CpG1[0])
		chr2_is_num=re.match("^[0-9]+$",CpG2[0])
		if chr1_is_num!=None and chr2_is_num!=None:
			#Les 2 chromosomes sont numeriques : on les compare numeriquement
			return int(CpG1[0]) - int(CpG2[0])
		elif chr1_is_num!=None:
			#Seule le chromosome 1 est numerique
			return -1
		elif chr2_is_num!=None:
			#Seule le chromosome 2 est numerique
			return +1
		else:
			#Les 2 chromosomes ne sont pas numeriques : on les compare sous forme de chaines
			if CpG1[0].__lt__(CpG2[0]):
				return -1
			else:
				return +1

#Fonction de "patch" pour coder en python3 ce que l'on faisait facilement en python2
def cmp_to_key(ma_fonction_de_comparaison):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) < 0
        def __gt__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) > 0
        def __eq__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) == 0
        def __le__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return ma_fonction_de_comparaison(self.obj, other.obj) != 0
    return K

"""
#Le Test
result=sorted([
			"2:1", "2:15", "2:2","2:3", "2:111", "2:4",
			"1:1", "1:15", "1:2","1:3", "1:111", "1:4",
			"X:1", "X:15", "X:2","X:3", "X:111", "X:4",
			"21:1", "21:15", "21:2","21:3", "21:111", "21:4",
			"Y:1", "Y:15", "Y:2","Y:3", "Y:111", "Y:4",
			"10:1", "10:15", "10:2","10:3", "10:111", "10:4",
	     ], key=cmp_to_key(numeric_compare))

print(result)

#Resultat
#['1:1', '1:2', '1:3', '1:4', '1:15', '1:111', '2:1', '2:2', '2:3', '2:4', '2:15', '2:111', '10:1', '10:2', '10:3', '10:4', '10:15', '10:111', '21:1', '21:2', '21:3', '21:4', '21:15', '21:111', 'X:1', 'X:2', 'X:3', 'X:4', 'X:15', 'X:111', 'Y:1', 'Y:2', 'Y:3', 'Y:4', 'Y:15', 'Y:111']
"""

#################################
# Parse arguments
#################################
parser = argparse.ArgumentParser()
parser.add_argument("--txt-output-file",help="pathname to the text output file")
parser.add_argument("--img-output-file",help="pathname to the image output file")
parser.add_argument("--set-file",help="pathname to each file corresponding to each entry set",nargs="+",action="append")
parser.add_argument("--set-name",help="name of each entry set (same order and same number as --set-file list)",nargs="*", action="append")
parser.add_argument("--keep-columns",help="name(s) of the column to report in venn text output file.",nargs="*", action="append")
parser.add_argument("--key-columns",help="Order number of the column used to build the key on which sets will be compared.",nargs="*", action="append")
parser.add_argument("--venn-title",help="Title displayed in Venn diagram")

args=parser.parse_args()

dico_set = {}
set_to_title = {1:'Only in Set_A',2:'Only in Set_B',3:'Common Set_A Set_B',4:'Only in Set_C',5:'Common Set_A Set_C',6:'Common Set_B Set_C',7:'Common Set_A Set_B Set_C'}

set_number = 0
liste_sets = []

#Get input files in a single list :
#See http://stackoverflow.com/questions/952914/making-a-flat-list-out-of-list-of-lists-in-python
input_files=[item for sublist in args.set_file for item in sublist]

input_titles=[]
if args.set_name is not None :
	input_titles=[item for sublist in args.set_name for item in sublist]

keep_columns=[]
if args.keep_columns is not None :
	keep_columns=[item for sublist in args.keep_columns for item in sublist]

key_columns=[1,2,3]
if args.key_columns is not None :
	key_columns=[item for sublist in args.key_columns for item in sublist]
	if len(key_columns)==1 and isinstance(key_columns[0],str) :
		#Try to decompose it if it has been provided as '--key-columns 1,2,3'
		key_columns=key_columns[0].split(",")

#Controm that key elemts are integer
for i in range(0,len(key_columns)) :
	try :
		key_columns[i]=int(key_columns[i])
		if key_columns[i] <= 0 : 
			parser.print_help()
			print "-----------\n"
			sys.exit("Key columns should be specified by column order numbers (e.g. --key-columns 1,2,3).\n"+
				 "Value '{0}' is not a positive number".format(key_columns[i])
			)
	except ValueError :
		parser.print_help()
		print "-----------\n"
		sys.exit("Key columns should be specified by column order numbers (e.g. --key-columns 1,2,3).\n"+
			 "Value '{0}' is not a number".format(key_columns[i])
		)

if len(input_files) != 2 and len(input_files) != 3 :
	parser.print_help()
	print "-----------\n"
	sys.exit("You provided {0} set entry files. This program only supports 2 or 3 ways Venn diagram.".format(len(input_files)))
	

if len(input_titles) != 0 and len(input_titles) != len(input_files) :
	parser.print_help()
	print "-----------\n"
	sys.exit("If you provide titles for the distinct data set, you should provide as many title as you have set entry files files.")

columns_kept={}
columns_kept_by_set={}
for idx in range(0,len(input_files)) :

	file=input_files[idx]

	#Determine set name
	if len(input_titles) != 0 :
		set_name=input_titles[idx]
	else : #Use the name of the file
		set_name=os.path.basename(file)
		pattern = re.search("^(.+)[.][^.]*$",set_name)
		if pattern is not None :
			set_name=pattern.group(1)
	liste_sets.append(set_name)

	indicateur = 2**set_number
	set_number += 1

	#on traite tous les fichiers txt entres en argument

	try :
		ifh = open(file)
	except IOError as exc:
		sys.exit("Cannot open input file '{0}' :\n{1}".format(file,exc))

	no_line=0
	for line in ifh:
		no_line+=1

		line = line.rstrip('\n\r')

		elmts = line.split('\t')

		if no_line == 1 :
			#Keep column names used to buil lthe key
			key_names=[]
			for key_idx in key_columns :
				key_names.append(elmts[key_idx-1])

			#Look for 'position of columns to keep
			i=0
			pos_fields={}
			columns_kept_by_set[set_name]=[]
			for elmt in elmts :
				if elmt in keep_columns :
					pos_fields[elmt]=i
					columns_kept_by_set[set_name].append(elmt)
				i+=1
			continue

		#Build key 
		key=""
		for key_idx in key_columns :
			if len(key)!=0 :
				key+="\t"
			key+=elmts[key_idx-1]
	
		if key not in columns_kept:
			columns_kept[key] = {}

		columns_kept[key][set_name] = {}
		for column_kept in keep_columns :
			if column_kept in pos_fields :
				columns_kept[key][set_name][column_kept] = elmts[pos_fields[column_kept]]
			else :
				columns_kept[key][set_name][column_kept] = None

		if key not in dico_set:
			dico_set[key] = 0

		dico_set[key] += indicateur

	ifh.close()

#On remplace les noms des sets A,B et C par les noms des fichiers en entree
for indicateur in set_to_title.keys():
	set_to_title[indicateur]=set_to_title[indicateur].replace("Set_A",liste_sets[0])
	set_to_title[indicateur]=set_to_title[indicateur].replace("Set_B",liste_sets[1])
	if (len(liste_sets)>=3) :
		set_to_title[indicateur]=set_to_title[indicateur].replace("Set_C",liste_sets[2])

if args.txt_output_file is not None :

	try :
		ofh = open(args.txt_output_file, "w") 
	except IOError as exc:
		sys.exit("Cannot create text output file '{0}' :\n{1}".format(args.txt_output_file,exc))

#### gestion ligne titre
# premiere colonne : Cle
# colonnes suivantes : 'only' ou 'common'
if set_number == 2:
	fin_sets=3
else:
	fin_sets=7

#Build line of headers
if args.txt_output_file is not None :
	#Header of column kept
	if len(keep_columns) !=0 :
		ofh.write('\t'*(len(key_names)-1))
		for indicateur in range(1,fin_sets+1):
			ofh.write('\t')
		for set_name in liste_sets :
			nb_columns=len(columns_kept_by_set[set_name])
			if nb_columns != 0 :
				ofh.write("\t"+set_name+'\t'*(nb_columns-1))
		ofh.write("\n")


	#Write key elements
	ofh.write("\t".join(key_names))

	for indicateur in range(1,fin_sets+1):
		ofh.write('\t')
		ofh.write(set_to_title[indicateur])

	for set_name in liste_sets :
		for column_kept in columns_kept_by_set[set_name] :
			ofh.write("\t"+column_kept)
	ofh.write('\n')

#Compute venn sets and produce text output file
venn_diagram = {}
for key in sorted(dico_set.keys(), key=cmp_to_key(numeric_compare)):
	# dict for graphic display (outputs a couple "condition:number of stars)
	if not set_to_title[dico_set[key]] in venn_diagram:
		venn_diagram[set_to_title[dico_set[key]]] = 1
	else:
		venn_diagram[set_to_title[dico_set[key]]] += 1

	if args.txt_output_file is not None :
		#Write key
		ofh.write(key)

		j = 1
		while j < dico_set[key]:
			ofh.write('\t' + ' ')
			j += 1
		ofh.write('\t*')

		while j < fin_sets:
			ofh.write('\t'+ ' ')
			j += 1

		for set_name in liste_sets :
			for column_kept in columns_kept_by_set[set_name] :
				ofh.write("\t")
				if key in columns_kept \
				and set_name in columns_kept[key] \
				and column_kept in columns_kept[key][set_name] :
					value=columns_kept[key][set_name][column_kept]
					if value is not None :
						ofh.write(value)

		ofh.write('\n')
   
  
if args.txt_output_file is not None :
	ofh.close() 

if args.img_output_file is None :
	#No Venn image requireed
	sys.exit(0)


# venn needs a tuple for graphics
# as venn_diagram is not sorted, we need to use the "set_to_title"
sub=[]

for condition_nb in set_to_title.values():
	if condition_nb in venn_diagram:
		sub.append(venn_diagram[condition_nb])
	else:
		sub.append(0)

# print tuple(sub)
# avec les 3 fichiers test, resultat attendu 
#Only in test1	Only in test2	Common test1 test2	Only in test3	Common test1 test3	Common test2 test3	Common test1 test2 test3
#(8, 6, 1, 7, 0, 2, 0)

plt.figure(figsize=(14,10)) # first number : width , second number : height
if len(liste_sets) == 2:
	v = venn2_unweighted(subsets = tuple(sub), set_labels = (liste_sets[0], liste_sets[1]))
elif len(liste_sets) == 3:
	v = venn3_unweighted(subsets = tuple(sub), set_labels = (liste_sets[0], liste_sets[1], liste_sets[2]))
	for text in v.set_labels: # file name size
		text.set_fontsize(12)
	for text in v.subset_labels: # numbers inside circles size
   		 text.set_fontsize(16)

if args.venn_title is not None :
	plt.title(args.venn_title)

# display title
#liste_sets_string = ', '.join(liste_sets)
#print liste_sets_string
#plt.title(liste_sets_string)

try :
	mpl.pyplot.savefig(args.img_output_file)
except ValueError as ve :
	print "Error occurred while trying to save Venn image in '{0}' file :\n".format(args.img_output_file)
	print ve
	sys.exit(1);
except IOError as exc:
	sys.exit("Cannot create image output file '{0}' :\n{1}".format(file,exc))




