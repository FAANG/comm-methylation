#
# Copyright (C) 2015 INRA
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

import time, json, random, copy, sys

def _bootstrap_remove_elts( OTU_count, nb_total_elts, nb_removed_elts ):
    """
    @summary : Randomly removes 'nb_removed_elts' elements in the OTU_count.
     @param OTU_count : [list] the number of elements by OTU. Example :
          [
            { 'id' : 'OTU_1', 'nb' : 10 },
            { 'id' : 'OTU_8', 'nb' : 0  }
          ]
     @param nb_total_elts : [int] the total number of elements in 'OTU_count'.
     @param nb_removed_elts : [int] the number of elements to remove.
    @return : [list, int] the new OTU_count and nb_total_elts.
    """
    if nb_total_elts <= nb_removed_elts :
        raise ValueError( "The Biom only contains " + str(nb_total_elts) + " elements. You cannot remove " + str(nb_removed_elts) + " elements." )
    new_OTU_count = copy.deepcopy( OTU_count )
    nb_curr_remaining_elts = nb_total_elts
    # For each element to remove
    for i in range(nb_removed_elts):
        elt_index = random.randint(1, nb_curr_remaining_elts)
        find = False
        OTU_idx = 0
        previous_elt = 0
        while not find:
            # If element to remove is an element of current OTU
            if elt_index <= (new_OTU_count[OTU_idx]["nb"] + previous_elt):
                find = True
                new_OTU_count[OTU_idx]["nb"] -= 1
            # Next OTU
            previous_elt += new_OTU_count[OTU_idx]["nb"]
            OTU_idx += 1
        nb_curr_remaining_elts -= 1
    return new_OTU_count, (nb_total_elts - nb_removed_elts)

def _bootstrap_selection( OTU_count, nb_total_elts, nb_selected_elts ):
    """
    @summary : Random sampling with replacement. Select 'nb_selected_elts' elements in the OTU_count.
     @param OTU_count : [list] the number of elements by OTU. Example :
          [
            { 'id' : 'OTU_1', 'nb' : 10 },
            { 'id' : 'OTU_8', 'nb' : 0  }
          ]
     @param nb_total_elts : [int] the total number of elements in 'OTU_count'.
     @param nb_selected_elts : [int] the number of elements to select.
    @return : [dict] the number of selected elements by OTU (the OTU with 0 selected elements are not in the dictionary).
    """
    if nb_selected_elts > nb_total_elts :
        sys.stderr.write( "[WARNING] The number of elements in the count is inferior at the number of selected elements.\n" )
    selected_OTU = dict()
    for i in range(nb_selected_elts):
        elt_index = random.randint(1, nb_total_elts)
        find = False
        OTU_idx = 0
        previous_elt = 0
        while not find:
            if elt_index <= (OTU_count[OTU_idx]["nb"] + previous_elt):
                find = True
                OTU_id = OTU_count[OTU_idx]["id"]
                if OTU_id in selected_OTU:
                    selected_OTU[OTU_id] += 1
                else:
                    selected_OTU[OTU_id] = 1
            previous_elt += OTU_count[OTU_idx]["nb"]
            OTU_idx += 1
    return selected_OTU


class DenseData( list ):
    def get_matrix_type( self ):
        """
        @summary : Retruns the type of matrix.
        @return : [str] The matrix type.
        """
        return "dense"

    def remove_col( self, remove_idx ):
        for row_idx in range(len(self)):
            del self.data[row_idx][remove_idx]

    def remove_row( self, remove_idx ):
        del self.data[remove_idx]

    def nb_at( self, row_idx, col_idx ):
        return self[row_idx][col_idx]

    def merge_col( self, sum_idx, added_idx ):
        for row in self:
            row[sum_idx] += row[added_idx]
        self.remove_col( added_idx )

    def get_col_sum( self, col_idx ):
        """
        @todo test
        """
        total = 0
        for current_row in self:
            total += current_row[col_idx]
        return total

    def get_row_sum( self, row_idx ):
        """
        @todo test
        """
        total = 0
        for current_col in self[row_idx]:
            total += current_col
        return total

    def clear( self ):
        """
        @summary : Clear data.
        """
        self = DenseData()

    def _to_list( self ):
        """
        @todo test
        """
        return self


class SparseData( dict ):
    def __init__( self, list=None ):
        ini_list = list if list is not None else list()
        for data in ini_list:
            if not data[0] in self:
                self[data[0]] = dict()
            self[data[0]][data[1]] = data[2]

    def _to_list( self ):
        """
        @summary : Returns counts ordered by row, by column.
        @return : [list] The counts ordered by row, by column.
        @example : [[ 1, 0, 250 ]   # The column 0 of the row 1 has a count of 250.
                     [ 8, 2, 100 ]   # The column 2 of the row 8 has a count of 100.
                     [ 9, 1, 521 ]]  # The column 1 of the row 9 has a count of 521.
        """
        sparse = list()
        for rows_idx in sorted(list(self.keys()), key=int):
            for columns_idx in sorted(self[rows_idx].keys()):
                sparse.append([ rows_idx, columns_idx, self[rows_idx][columns_idx] ])
        return sparse

    def get_matrix_type( self ):
        """
        @summary : Retruns the type of matrix.
        @return : [str] The matrix type.
        """
        return "sparse"

    def remove_col( self, remove_idx ):
        """
        @summary : Remove all the count for the column provided.
         @param remove_idx : [int] The real index of the column to remove.
        """
        for rows_idx in list(self.keys()):
            # Remove data
            if remove_idx in self[rows_idx]:
                del self[rows_idx][remove_idx]
            # Change index
            row_columns_idx = sorted( list(self[rows_idx].keys()), key=int )
            for column_idx in row_columns_idx:
                if column_idx > remove_idx:
                    self[rows_idx][column_idx -1] = self[rows_idx][column_idx]
                    del self[rows_idx][column_idx]

    def remove_row( self, remove_idx ):
        """
        @summary : Remove all the count for the row provided.
         @param remove_idx : [int] The real index of the row to remove.
        """
        # Remove data
        if remove_idx in self:
            del self[remove_idx]
        # Change indexes
        all_rows_idx = sorted( list(self.keys()), key=int )
        for row_idx in all_rows_idx:
            if row_idx > remove_idx:
                self[row_idx - 1] = self[row_idx]
                del self[row_idx]

    def merge_col( self, sum_idx, added_idx ):
        """
        @summary : Merge two columns. The count of each row of the first column (sum_idx) becomes the sum of the values of the two columns ; the second column is deleted.
         @param sum_idx : [int] The index of the first column to merge. This column is replaced by the new merged column.
         @param added_idx : [int] The index of the second column to merge. This column is deleted after the process.
        """
        # Merge counts
        added_values = dict()
        for row_idx in list(self.keys()):
            if added_idx in self[row_idx]:
                self.add( row_idx, sum_idx, self[row_idx][added_idx] )
        # Remove column
        self.remove_col( added_idx )
    
    def nb_at( self, row_idx, col_idx ):
        """
        @return : [int] The count for the column col_idx in row row_idx.
         @param row_idx : [int] The index of the row.
         @param col_idx : [int] The index of the column.
        """
        nb = 0
        if row_idx in self and col_idx in self[row_idx]:
            nb = self[row_idx][col_idx]
        return nb

    def get_col_sum( self, col_idx ):
        """
        @return : [int] The sum of count for the column col_idx.
         @param col_idx : [int] The index of the column.
        """
        total = 0
        for row_idx in list(self.keys()):
            if col_idx in self[row_idx]:
                total += self[row_idx][col_idx]
        return total

    def get_row_sum( self, row_idx ):
        """
        @return : [int] The sum of count for the row row_idx.
         @param row_idx : [int] The index of the row.
        """
        total = 0
        if row_idx in self:
            for column_idx in list(self[row_idx].keys()):
                total += self[row_idx][column_idx]
        return total

    def row_to_array( self, row_idx, nb_col ):
        """
        @return : [list] The count for the row for each column.
                   Example : '[0, 2, 0, 0]' only the second column has this observation.
         @param row_idx : [int] The index of the row.
         @param nb_col : [int] The expected number of columns.
        """
        array = [0 for current in range(nb_col)]
        if row_idx in self:
            for column_idx in sorted( self[row_idx].keys() ):
                array[column_idx] = self[row_idx][column_idx]
        return array

    def add( self, row_idx, col_idx, value ):
        """
        @summary : Add the 'value' to the count for the column col_idx in row row_idx.
         @param row_idx : [int] The index of the row.
         @param col_idx : [int] The index of the column.
         @param value : [int] The value to add.
        """
        if not row_idx in self:
            self[row_idx] = { col_idx : 0 }
        elif not col_idx in self[row_idx]:
            self[row_idx][col_idx] = 0
        self[row_idx][col_idx] += value
        
    def subtract( self, row_idx, col_idx, value ):
        """
        @summary : Subtract the 'value' to the count for the column col_idx in row row_idx.
         @param row_idx : [int] The index of the row.
         @param col_idx : [int] The index of the column.
         @param value : [int] The value to subtract.
        """
        if row_idx in self and col_idx in self[row_idx] and self[row_idx][col_idx] >= value:
            self[row_idx][col_idx] -= value
        else:
            raise Exception( "'" + str(value) + "' cannot be subtract from row " + str(row_idx) + " column " + str(col_idx) + "." ) 
    
    def change( self, row_idx, col_idx, value ):
        """
        @summary : Change the 'value' to the count for the column col_idx in row row_idx.
         @param row_idx : [int] The index of the row.
         @param col_idx : [int] The index of the column.
         @param value : [int] The new value.
        """
        if value != 0:
            if not row_idx in self:
                self[row_idx] = { col_idx : value }
            else:
                self[row_idx][col_idx] = value
        else:
            if row_idx in self and col_idx in self[row_idx]:
                del self[row_idx][col_idx]
    
    def random_by_col( self, col_idx ):
        """
        """
        elt_index = random.randint(1, self.get_col_sum(col_idx))
        find = False
        row_idx = 0
        previous_elt = 0
        while not find:
            current_nb = previous_elt + self.nb_at( row_idx, col_idx )
            if elt_index <= current_nb:
                find = True
            # Next row
            previous_elt = current_nb
            row_idx += 1
        return( row_idx -1 )

    def add_row( self ):
        pass # Nothing to do

    def add_column( self ):
        pass # Nothing to do


class Biom:
    """
    @summary : Store biological sample by observation contingency tables.
    @see : https://github.com/biom-format
    """
    def __init__( self, id=None, format="Biological Observation Matrix 1.0.0-dev", 
                  format_url="http://biom-format.org", type="OTU table", generated_by=None, 
                  date=None, rows=None, columns=None, matrix_type="dense", matrix_element_type="int", 
                  data=None ):
        """
        @param id : [int]
        @param format : [str]
        @param format_url : [str]
        @param type : [str]
        @param generated_by : [str]
        @param date : [str]
        @param rows : [list]
        @param columns : [list]
        @param matrix_type : [str]
        @param matrix_element_type : [str]
        @param data : [list]
        """
        self.id = id
        self.format = format
        self.format_url = format_url
        self.type = type
        self.generated_by = generated_by
        self.date = date if date is not None else time.strftime('%y-%m-%dT%H:%M:%S',time.localtime())
        self.rows = rows if rows is not None else list()
        self.columns = columns if columns is not None else list()
        self.matrix_element_type = matrix_element_type
        ini_data = data if data is not None else list()
        if matrix_type == "dense":
            self.data = DenseData( ini_data )
        else:
            self.data = SparseData( ini_data )

    def __str__(self):
        return str( self.__dict__ )

    def __repr__(self):
        return str( self.__dict__ )

    def observations_counts(self):
        """
        @summary : Return the list of the observations counts.
        @return : [list] the observation ID and the observation count for each observation.
                  Example :
                  [
                    ["OTU_1", 128],
                    ["OTU_2", 8]
                  ]
        """
        for observation_idx in range(len(self.rows)):
            yield self.rows[observation_idx]['id'], self.data.get_row_sum(observation_idx)

    def remove_observations( self, observations_names ):
        """
        @summary : Removes the specified observations.
         @param observations_names : [list] The IDs of the observations to remove. 
        """
        for current_observation in observations_names :
            observation_idx = self.find_idx( self.rows, current_observation )
            # Remove OTU from the self.rows
            del self.rows[observation_idx]
            # Remove OTU from the self.data
            self.data.remove_row( observation_idx )

    def reset_count_by_replicates_evidence( self, samples_names, min_evidence_nb=2 ):
        """
        @summary : Puts to 0 the counts of an observation for all samples in a replicate if the 
                    number of samples with this observation is lower than 'min_evidence_nb' in 
                    the replicate.
                    example : with min_evidence_nb = 2 and 2 triplicates (A and B)
                       Before process
                             sample_A_1 sample_A_2 sample_A_3 sample_B_1 sample_B_2 sample_B_3
                         obs     1           1           0         0          0          2
                       After process
                             sample_A_1 sample_A_2 sample_A_3 sample_B_1 sample_B_2 sample_B_3
                         obs     1           1           0         0          0          0
        @param samples_names : [list] The names of the replicates.
        @param min_evidence_nb : [int] The minimun number of replicates with the observation.
        """
        samples_idx = [self.find_idx(self.columns, sample) for sample in samples_names]
        # For each observation
        for row_idx in range( len(self.rows) ):
            obs_evidence = 0
            # Process evidence number
            for col_idx in samples_idx:
                if self.data.nb_at(row_idx, col_idx) > 0: # if count > 0
                    obs_evidence += 1
            # If the evidence is insufficient
            if obs_evidence < min_evidence_nb and obs_evidence > 0:
                # for each sample
                for col_idx in samples_idx:
                    # Set observation count to 0
                    self.data.change( row_idx, col_idx, 0 )

    def filter_OTU_by_count( self, min_nb, max_nb=None ):
        """
        @summary : Filter observations on count value.
         @param min_nb : [int] The observations with a count inferior to 'min_nb' is removed.
         @param max_nb : [int] The observations with a count superior to 'min_nb' is removed.
        """
        removed_obs_names = list()
        for observation_idx in range( len(self.rows) ):
            observation_count = self.data.get_row_sum( observation_idx )
            if observation_count < min_nb or (max_nb is not None and observation_count > max_nb):
                removed_obs_names.append( self.rows[observation_idx]["id"] )
        self.remove_observations( removed_obs_names )

    def merge_samples( self, samples, merged_sample_id=None ):
        """
        @summary : Merge data and metadata of a list of samples.
         @param samples : [list] Samples to merge.
         @param merged_sample_id : [str] Name for the new meta-sample.
        """
        # Preprocess final_sample
        final_idx = self.find_idx(self.columns, samples[0])
        final_sample = self.columns[final_idx]
        if final_sample['metadata'] is not None:
            metadata_names = list(final_sample['metadata'].keys())
            for metadata_name in metadata_names:
                final_sample['metadata'][final_sample['id'] + ":" + metadata_name] = final_sample['metadata'][metadata_name]
                del final_sample['metadata'][metadata_name]
        else:
            final_sample['metadata'] = dict()
        # Merge
        for current_name in samples[1:]:
            final_idx = self.find_idx(self.columns, samples[0])
            # Find sample
            current_idx = self.find_idx(self.columns, current_name)
            current_sample = self.columns[current_idx]
            # Update metadata history
            if merge_history in final_sample['metadata']:
                final_sample['metadata']['merge_history'] += " AND " + current_sample['id']
            else:
                final_sample['metadata']['merge_history'] = final_sample['id'] + " AND " + current_sample['id']
            # Merge metadata
            if current_sample['metadata'] is not None:
                for metadata_name in current_sample['metadata']:
                    final_sample['metadata'][current_sample['id'] + ":" + metadata_name] = current_sample['metadata'][metadata_name]
            # Merge data
            self.data.merge_col( final_idx, current_idx )
            # Remove sample from the self.columns
            del self.columns[current_idx]
        # If rename final sample
        if merged_sample_id is not None:
            final_sample['id'] = merged_sample_id

    def find_idx( self, subject, query_name ):
        """
        @summary : Returns the index of the query.
         @param subject : [list] The Biom.rows or Biom.columns where query is seach.
         @param query_name : [str] The id of the element (ex : "OTU_0012").
        @return : [int] The index of the element.
        @todo : Change 'subject' by 'subject_type'.
        """
        find_idx = None
        idx = 0
        while idx < len(subject) and find_idx is None:
            if subject[idx]['id'] == query_name:
                find_idx = idx
            idx += 1
        if find_idx is None:
            raise ValueError( "'" + query_name + "' doesn't exist." )
        return find_idx

    def add_metadata( self, subject_name, metadata_name, metadata_value, subject_type="sample"):
        """
        @summary : Add a metadata on subject (a sample or an observation).
         @param subject_name : [str] Metadata is added to the sample/observation with this name. 
         @param metadata_name : [str] The metadata category (ex : 'taxonomy').
         @param metadata_name : [str] The value of metadata (ex : 'Bacteria').
         @param subject_type : [str] The type of subject : "sample" or "observation".
        """
        # Select subject container
        if subject_type == "sample":
            subject_list = self.columns
        elif subject_type == "observation":
            subject_list = self.rows
        else:
            raise ValueError( "'" + subject_type + "' is an invalid subject type for metadata. Metadata must be add to 'observation' or 'sample'." )
        # Find subject
        try:
            subject_idx = self.find_idx( subject_list, subject_name )
        # Subject does not exist
        except ValueError:
            sys.stderr.write("[WARNING] The metadata named '" + metadata_name + "' can't be added to sample '" + subject_name + "' because it does not exist.\n")
        # Subject exists
        else:
            if subject_list[subject_idx]['metadata'] is None:
                subject_list[subject_idx]['metadata'] = dict()
            elif metadata_name in subject_list[subject_idx]['metadata']:
                sys.stderr.write("[WARNING] You erase previous value of the metadata named '" + metadata_name + "' in " + subject_name + " (OLD:'" + str(subject_list[subject_idx]['metadata'][metadata_name]) + "' => NEW:'" + str(metadata_value) + "').\n")
            subject_list[subject_idx]['metadata'][metadata_name] = metadata_value

    def to_JSON( self ):
        """
        @summary : Return a json format for the data store in the Biom object.
        @return : [str] The json.
        """
        self.shape = [
                       len(self.rows),
                       len(self.columns)
        ]
        self.matrix_type = self.data.get_matrix_type()
        save_data = self.data
        self.data = save_data._to_list()
        json_str = json.dumps( self, default=lambda o: o.__dict__, sort_keys=False, indent=4 )
        self.data = save_data
        del self.shape
        del self.matrix_type
        return json_str

    def remove_samples( self, samples_names ):
        """
        @summary : Removes sample(s) from biom.
         @param samples_names : [str] The name of the sample to rename.
        """
        for current_sample in samples_names :
            sample_idx = self.find_idx( self.columns, current_sample )
            # Remove sample from the self.columns
            del self.columns[sample_idx]
            # Remove sample from the self.data
            self.data.remove_col( sample_idx )

    def subtract_count( self, observation_name, sample_name, value ):
        """
        @summary : Subtract a value to the count for one observation of one sample.
         @param observation_name : [str] The observation name.
         @param sample_name : [str] The sample name.
         @param value : [int] The value to subtract.
        """
        row_idx = self.find_idx( self.rows, observation_name )
        col_idx = self.find_idx( self.columns, sample_name )
        self.data.subtract( row_idx, col_idx, value )

    def add_count( self, observation_name, sample_name, value ):
        """
        @summary : Add a value to the count for one observation of one sample.
         @param observation_name : [str] The observation name.
         @param sample_name : [str] The sample name.
         @param value : [int] The value to add.
        """
        row_idx = self.find_idx( self.rows, observation_name )
        col_idx = self.find_idx( self.columns, sample_name )
        self.data.add( row_idx, col_idx, value )

    def add_observation( self, observation_name, metadata=None ):
        """
        @summary : Add one observation in biom.
         @param observation_name : [str] The observation name.
         @param metadata : [dict] The metadata (keys : metadata names ; values : metadata values).
        """
        ini_metadata = metadata if metadata is not None else dict()
        try:
            self.find_idx( self.rows, observation_name )
        # Observation doesn't exist
        except ValueError:
            self.rows.append( {'id':observation_name, 'metadata':None } )
            self.data.add_row()
            for metadata_name in list(ini_metadata.keys()):
                self.add_metadata( observation_name, metadata_name, ini_metadata[metadata_name], "observation" )
        # Observation already exists
        else:
            raise ValueError( "The observation '" + observation_name + "' already exists." )

    def add_sample( self, sample_name, metadata=None ):
        """
        @summary : Add one sample in biom.
         @param sample_name : [str] The sample name.
         @param metadata : [dict] The metadata (keys : metadata names ; values : metadata values).
        """
        ini_metadata = metadata if metadata is not None else dict()
        try:
            self.find_idx( self.columns, sample_name )
        # Sample doesn't exist
        except ValueError:
            self.columns.append( {'id':sample_name, 'metadata':None } )
            self.data.add_column()
            for metadata_name in list(ini_metadata.keys()):
                self.add_metadata( sample_name, metadata_name, ini_metadata[metadata_name], "sample" )
        # Sample already exists
        else:
            raise ValueError( "The sample '" + sample_name + "' already exists." )

    def get_samples_names( self ):
        """
        @summary : Returns a generator to iterate on samples names.
        @return : [generator] the generator to iterate on samples names.
        """
        for col in self.columns:
            yield col["id"]

    def get_observations_names( self ):
        """
        @summary : Returns a generator to iterate on observations names.
        @return : [generator] the generator to iterate on observations names.
        """
        for col in self.rows:
            yield col["id"]

    def _hash_OTU_by_sample( self ):
        """
        @summary : Count the number of elements by OTU.
        @return : [list, int] the number of elements by OTU and the total number of elements.
              Example for the number of elements by OTU :
              [
                { 'id' : 'OTU_1', 'nb' : 10 },
                { 'id' : 'OTU_8', 'nb' : 0  }
              ]
        """
        nb_OTU_by_sample = { col['id']:list() for col in self.columns }
        sum_by_sample = { col['id']:0 for col in self.columns }
        for row_idx in range(len(self.rows)):
            for columns_idx in range(len(self.columns)):
                nb = self.data.nb_at( row_idx, columns_idx )
                sample_id = self.columns[columns_idx]['id']
                sum_by_sample[sample_id] += nb
                nb_OTU_by_sample[sample_id].append( { "id" : self.rows[row_idx]["id"],
                                                      "nb" : nb } )
        return nb_OTU_by_sample, sum_by_sample

    def bootstrap_by_sample( self, nb_selected_elts, nb_removed_elts, nb_selection_round=1000 ):
        """
        @summary : Replaces data of the sample by random sampling with replacement in the sample.
         @param nb_selected_elts : [int] Number of elements selected on sampling.
         @param nb_removed_elts : [int] Number of elements removed of the initial set before random sampling.
         @param nb_selection_round : [int] Number of sampling round.
        @example : nb_removed_elts = 100, nb_selected_elts = 10, nb_selection_round = 2 
                    and sample A = { sea:800, lake:150, air:50 }
                    ROUND 1   remove  selection
                     sea      720        9
                     lake     145        1
                     air      35         0
                    ROUND 2   remove  selection
                     sea      730        7
                     lake     130        2
                     air      40         1
                    Result
                     sea      16
                     lake     3
                     air      1
        """
        nb_OTU_by_sample, sum_by_sample = self._hash_OTU_by_sample()
        self.data.clear()
        if self.generated_by is None:
            self.generated_by = ""
        else:
            self.generated_by += ' | '
        self.generated_by += "sampling[delete : " + str(nb_removed_elts) + "; select : " + str(nb_selected_elts) + "; round : " + str(nb_selection_round) + "]" 
        for i in range(nb_selection_round):
            for current_sample in self.columns:
                sample_id = current_sample['id']
                # Random remove
                remaining_OTU_count, nb_elts = _bootstrap_remove_elts( nb_OTU_by_sample[sample_id], sum_by_sample[sample_id], nb_removed_elts )
                # Random selection 
                selected = _bootstrap_selection( remaining_OTU_count, nb_elts, nb_selected_elts )
                # Add to new_data
                for OTU_id in list(selected.keys()):
                    OTU_idx = self.find_idx( self.rows, OTU_id )
                    sample_idx = self.find_idx( self.columns, current_sample['id'] )
                    self.data.add( OTU_idx, sample_idx, selected[OTU_id] )
    
    def random_obs_by_sample( self, sample_name ):
        sample_idx = self.find_idx(self.columns, sample_name)
        return self.rows[self.data.random_by_col(sample_idx)]

    def get_sample_count( self, sample_name ):
        return self.data.get_col_sum( self.find_idx(self.columns, sample_name) )

    def to_count( self ):
        """
        @summary : Returns the count of observations by sample.
        @return : [generator] The generator to iterate on observations. Each observation is a list of count 
                  by sample.
                  Example : [1, 0] # Iteration 1 : sample_1 has one observation_1, sample_2 has zero observation_1
                            [1, 8] # Iteration 2 : sample_1 has one observation_2, sample_2 has eight observation_2
        """
        nb_rows = len(self.rows)
        nb_columns = len(self.columns)
        for row_idx in range(nb_rows):
            yield self.data.row_to_array( row_idx, nb_columns )

    def to_count_table( self ):
        """
        @summary : Returns the count of observations by sample with titles.
        @return : [generator] The generator to iterate on observations. First line is a title.
                  Example : ['#Observation', 'Sample1', 'Sample2'] # Iteration 1 : title
                            ['GG_OTU_1', 1, 0] # Iteration 2 : Sample1 has one GG_OTU_1, Sample1 has zero GG_OTU_1
                            ['GG_OTU_2', 1, 8] # Iteration 3 : Sample2 has one GG_OTU_2, Sample2 has eight GG_OTU_2
        """
        # Return Title
        yield ["#Observation"] + [col['id'] for col in self.columns]
        # Return lines
        row_idx = 0
        for row in self.to_count():
            OTU_name = self.rows[row_idx]['id']
            row_idx += 1
            yield [OTU_name] + row


class BiomIO:
    """
    Reader/Writer for the Biom format.
    The BIOM file format is a json format designed to be a general-use format for representing biological sample by observation contingency tables.
    BIOM is a recognized standard for the Earth Microbiome Project and is a Genomics Standards Consortium candidate project.
    @see : https://github.com/biom-format
    """
    @staticmethod
    def from_count_table( count_file, generated_by=None ):
        """
        @summary : Return an object 'Biom' from a count table.
         @param count_file : [str] The path of the count file.
                             Format :
                              #Cluster_ID<TAB>sample1<TAB>sample2
                              OTU1<TAB>8<TAB>10
                              ...
         @param generated_by : [str] The method/software used to generate data.
        @return [Biom] The Biom object.
        """
        biom = Biom()
        biom.data = SparseData()
        biom.generated_by = generated_by

        count_fh = open( count_file )
        row_idx = 0
        for line in count_fh:
            line = line.strip()
            line_fields = line.split()
            # Title line
            if line.startswith('#'):
                for sample in line_fields[1:]:
                    # Load sample (biom.columns)
                    biom.columns.append( { 
                                     'id':sample,
                                     'metadata':None
                    })
            # OTU line
            else:
                # Load OTU (biom.rows)
                biom.rows.append( {
                                    'id':line_fields[0],
                                    'metadata':None
                })
                # Load count (biom.data)
                col_idx = 0
                for count in line_fields[1:]:
                    if int(count) != 0:
                        biom.data.add( row_idx, col_idx, int(count) )
                    col_idx += 1
                row_idx += 1
        count_fh.close()

        return biom

    @staticmethod
    def from_json( path ):
        """
        @summary : Return an object 'Biom' from a biom file.
         @param path : [str] The path of the biom file.
        @return [Biom] The Biom object.
        """
        json_data = open( path )
        python_dict = json.load( json_data )
        json_data.close()

        return Biom( python_dict["id"], 
                     python_dict["format"], 
                     python_dict["format_url"],
                     python_dict["type"], 
                     python_dict["generated_by"],
                     python_dict["date"],
                     python_dict["rows"],
                     python_dict["columns"],
                     python_dict["matrix_type"],
                     python_dict["matrix_element_type"],
                     python_dict["data"] )

    @staticmethod
    def write( path, biom ):
        """
        @summary : Write a biom file from a 'Biom'.
         @param path : [str] The path of the biom file.
         @param biom : [Biom] The Biom object to write.
        """
        out_fh = open( path, "w" )
        out_fh.write( biom.to_JSON() )
        out_fh.close()

    @staticmethod
    def write_count_table( path, biom ):
        """
        @summary : Write count table from an object 'Biom'.
         @param path : [str] The path of the biom file.
         @param biom : [Biom] The Biom object to write.
        """
        out_fh = open( path, "w" )
        for line in biom.to_count_table():
            out_fh.write( "\t".join(map(str, line)) + "\n" )
        out_fh.close()

    @staticmethod
    def write_krona_table( path, biom ):
        """
        @todo test
        """
        out_fh = open( path, "w" )
        for idx in range(len(biom.rows)):
            count = biom.data.get_row_sum( idx )
            tax = biom.rows[idx]["metadata"]["taxonomy"]
            if isinstance(tax, list) or isinstance(tax, tuple):
                tax = "\t".join( map(str, tax) )
            else:
                tax = str( tax )
            tax = "\t".join( map(str.strip, tax.split(";")) ) # Replace space separator between ranks by tabulation
            out_fh.write( str(count) + "\t" + tax + "\n" )
        out_fh.close()

    @staticmethod
    def write_krona_table_by_sample( path, biom, sample ):
        """
        @todo test
        """
        out_fh = open( path, "w" )
        col_idx = biom.find_idx( biom.columns, sample )
        for row_idx in range(len(biom.rows)):
            count = biom.data.nb_at( row_idx, col_idx )
            if count > 0:
                taxonomy = biom.rows[row_idx]["metadata"]["taxonomy"]
                cleaned_taxonomy = None
                if isinstance(taxonomy, list) or isinstance(taxonomy, tuple):
                    taxa_list = list()
                    for taxon in taxonomy:
                        if not str(taxon).lower().startswith("unknown "):
                            taxa_list.append( taxon )
                    cleaned_taxonomy = "\t".join(taxa_list)
                else:
                    cleaned_taxonomy = "\t".join( map(str.strip, taxonomy.split(";")) )
                out_fh.write( str(count) + "\t" + cleaned_taxonomy + "\n" )
        out_fh.close()

    @staticmethod
    def load_metadata( biom, metadata_file, subject_type="sample", types=None, list_sep=None ):
        """
        @summary : Add to biom several metadata from metadata file.
         @param biom : [Biom] The Biom object to update.
         @param metadata_file : [str] The path of the metadata file.
                                Format :
                                #TITLE<TAB>Metadata_1_name<TAB>Metadata_2_name
                                Subject_name<TAB>Metadata_1_value<TAB>Metadata_2_value
                                ...
         @param subject_type : [str] The type of subject : "sample" or "observation".
         @param types : [dict] Types for of the metadata values ("str", "int", "float").
                        Example :
                        {
                          'confidence' : 'float',
                          'rank'       : 'int'
                        }
         @param list_sep : [dict] Separator if the metadata is a list.
                        Example :
                        {
                          'taxonomy'      : ';', # Bacteria;Proteobacteria
                          'environnement' : '/'  # Sea/Ocean
                        }
        """
        ini_types = types if types is not None else dict()
        ini_list_sep = list_sep if list_sep is not None else dict()
        metadata_fh = open( metadata_file )
        metadata = list()
        # Names and type of metadata
        title_line = metadata_fh.readline().strip()
        title_fields = title_line.split()
        for metadata_name in title_fields[1:]:
            metadata_type = "str"
            if metadata_name in ini_types:
                metadata_type = ini_types[metadata_name]
            metadata_list_sep = None
            if metadata_name in ini_list_sep:
                metadata_list_sep = ini_list_sep[metadata_name]
            metadata.append( {
                              'name'     : metadata_name,
                              'type'     : metadata_type,
                              'list_sep' : metadata_list_sep
            })
        # Values of metadata
        for line in metadata_fh:
            line = line.strip()
            if not line.startswith('#'):
                line_fields = line.split()
                metadata_subject = line_fields[0]
                title_idx = 0
                for metadata_value in line_fields[1:]:
                    # Manage cast metadata value
                    if metadata[title_idx]['type'] == "str":
                        cast = str
                    elif metadata[title_idx]['type'] == "int":
                        cast = int
                    elif metadata[title_idx]['type'] == "float":
                        cast = float
                    else:
                        raise ValueError( "'" + metadata[title_idx]['type'] + "' is an invalid type for metadata. Metadata must be 'str' or 'int' or 'float'." )
                    # Manage split
                    if metadata[title_idx]['list_sep'] is None:
                        metadata_value = cast( metadata_value )
                    else:
                        metadata_value = [cast(value) for value in metadata_value.split(metadata[title_idx]['list_sep'])]
                    # Add metadata
                    biom.add_metadata( metadata_subject, metadata[title_idx]['name'], metadata_value, subject_type)
                    # Next medata title
                    title_idx += 1