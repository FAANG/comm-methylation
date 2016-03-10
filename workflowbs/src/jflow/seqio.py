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

__author__ = 'Plateforme bioinformatique Midi Pyrenees'
__copyright__ = 'Copyright (C) 2009 INRA'
__license__ = 'GNU General Public License'
__version__ = '1.0'
__email__ = 'support.genopole@toulouse.inra.fr'
__status__ = 'beta'


from collections import namedtuple
import sys
import struct
import os
import io
str = str
from codecs import getreader, getwriter

if sys.version_info < (2, 7):
    buffered_reader = lambda x: x
else:
    buffered_reader = io.BufferedReader

from os.path import splitext
import sys, gzip, bz2


def xopen(filename, mode='r'):
    """
    Replacement for the "open" function that can also open
    files that have been compressed with gzip. If the filename ends with .gz,
    the file is opened with gzip.open(). If it doesn't, the regular open()
    is used. If the filename is '-', standard output (mode 'w') or input
    (mode 'r') is returned.
    """
    assert isinstance(filename, str)
    if filename == '-':
        return sys.stdin if 'r' in mode else sys.stdout
    if filename.endswith('.gz'):
        if sys.version_info[0] < 3:
            if 'r' in mode:
                return buffered_reader(gzip.open(filename, mode))
            else:
                return gzip.open(filename, mode)
        else:
            if 'r' in mode:
                return getreader('ascii')(gzip.open(filename, mode))
            else:
                return getwriter('ascii')(gzip.open(filename, mode))
    elif filename.endswith('.bz2'):
        if sys.version_info[0] < 3:
            return bz2.BZ2File(filename, mode)
        else:
            if 'r' in mode:
                return getreader('ascii')(bz2.BZ2File(filename, mode))
            else:
                return getwriter('ascii')(bz2.BZ2File(filename, mode))
    else:
        return open(filename, mode)

Sequence = namedtuple("Sequence", "name description sequence qualities")

class FormatError(Exception):
    """
    Raised when an input file (FASTA or FASTQ) is malformatted.
    """
    pass


class FileWithPrependedLine(object):
    """
    A file-like object that allows to "prepend" a single
    line to an already opened file. That is, further
    reads on the file will return the provided line and
    only then the actual content. This is needed to solve
    the problem of autodetecting input from a stream:
    As soon as the first line has been read, we know
    the file type, but also that line is "gone" and
    unavailable for further processing.
    """
    def __init__(self, file, line):
        """
        file is an already opened file-like object.
        line is a single string (newline will be appended if not included)
        """
        if not line.endswith('\n'):
            line += '\n'
        self.first_line = line
        self.file = file

    def __iter__(self):
        yield self.first_line
        for line in self.file:
            yield line


class UnknownFileType(Exception):
    """
    Raised when SequenceReader could not autodetect the file type.
    """
    pass


def SequenceReader(file, colorspace=False, fileformat=None):
    """
    Reader for FASTA, FASTQ, and SFF files that autodetects the file format.
    Returns either an instance of FastaReader, FastqReader, SFFReader
    depending on file type.

    The autodetection can be skipped by setting fileformat to the string
    'fasta', 'fastq' or sff

    file is a filename or a file-like object.
    If file is a filename, then .gz files are supported.
    If the file name is available, the file type is detected
    by looking at the file name.
    If the file name is not available (for example, reading
    from standard input), then the file is read and the file
    type determined from the content.
    """
    if fileformat is not None:
        fileformat = fileformat.lower()
        if fileformat == 'fasta':
            return FastaReader(file)
        elif fileformat == 'fastq':
            return FastqReader(file)
        elif fileformat == "sff":
            return SFFReader(file)
        else:
            raise UnknownFileType("File format {} is unknown (expected 'fasta', 'fastq' or 'sff').".format(fileformat))

    name = None
    if file == "-":
        file = sys.stdin
    elif isinstance(file, str):
        name = file
    elif hasattr(file, "name"):
        name = file.name
    if name is not None:
        if name.endswith('.gz'):
            name = name[:-3]
        name, ext = splitext(name)
        ext = ext.lower()
        if ext in ['.fasta', '.fa', '.fna', '.csfasta', '.csfa']:
            return FastaReader(file)
        elif ext in ['.fastq', '.fq']:
            return FastqReader(file, colorspace)
        elif ext in ['.sff']:
            return SFFReader(file)
        else:
            raise UnknownFileType("Could not determine whether this is FASTA, FASTQ or SFF: file name extension {} not recognized".format(ext))

    # No name available.
    # Assume that 'file' is an open file
    # and autodetect its type by reading from it.
    # TODO: test if binarie file for SFFReader
    for line in file:
        if line.startswith('#'):
            # Skip comment lines (needed for csfasta)
            continue
        if line.startswith('>'):
            return FastaReader(FileWithPrependedLine(file, line))
        if line.startswith('@'):
            return FastqReader(FileWithPrependedLine(file, line), colorspace)
    raise UnknownFileType("File is neither FASTQ nor FASTA.")



class FastaReader(object):
    """
    Reader for FASTA files.
    """
    def __init__(self, file, wholefile=False, keep_linebreaks=False):
        """
        file is a filename or a file-like object.
        If file is a filename, then .gz files are supported.
        If wholefile is True, then it is ok to read the entire file
        into memory. This is faster when there are many newlines in
        the file, but may obviously need a lot of memory.
        keep_linebreaks -- whether to keep the newline characters in the sequence
        """
        if isinstance(file, str):
            file = xopen(file, "r")
        self.fp = file
        self.wholefile = wholefile
        self.keep_linebreaks = keep_linebreaks
        assert not (wholefile and keep_linebreaks), "not supported"

    def __iter__(self):
        """
        Return instances of the Sequence class.
        The qualities attribute is always None.
        """
        return self._wholefile_iter() if self.wholefile else self._streaming_iter()

    def _streaming_iter(self):
        """
        Read next entry from the file (single entry at a time).

        # TODO this can be quadratic since += is used for the sequence string
        """
        name = None
        seq = ""
        appendchar = '\n' if self.keep_linebreaks else ''
        for line in self.fp:
            # strip() should also take care of DOS line breaks
            line = line.strip()
            if line and line[0] == ">":
                if name is not None:
                    assert self.keep_linebreaks or seq.find('\n') == -1
                    id = name.split()[0]
                    desc = " ".join(name.split()[1:])
                    yield Sequence(id, desc, seq, None)
                name = line[1:]
                seq = ""
            else:
                seq += line + appendchar
        if name is not None:
            assert self.keep_linebreaks or seq.find('\n') == -1
            id = name.split()[0]
            desc = " ".join(name.split()[1:])
            yield Sequence(id, desc, seq, None)

    def _wholefile_iter(self):
        """
        This reads in the entire file at once, but is faster than the above code when there are lots of newlines.
        The idea comes from the TAMO package (http://fraenkel.mit.edu/TAMO/), module TAMO.seq.Fasta (author is
        David Benjamin Gordon).
        """
        wholefile = self.fp.read()
        assert len(wholefile) != 0 and wholefile[0] == '>', "FASTA file must start with '>'"
        parts = wholefile.split('\n>')
        # first part has '>' in front
        parts[0] = parts[0][1:]
        for part in parts:
            lines = part.split('\n', 1)
            id = lines[0].split()[0]
            desc = " ".join(lines[0].split()[1:])
            yield Sequence(id, desc, lines[1].replace('\n', ''), None)

    def __enter__(self):
        if self.fp is None:
            raise ValueError("I/O operation on closed FastaReader")
        return self

    def __exit__(self, *args):
        self.fp.close()


class FastqReader(object):
    """
    Reader for FASTQ files. Does not support multi-line FASTQ files.
    """
    def __init__(self, file, colorspace=False):
        """
        file is a filename or a file-like object.
        If file is a filename, then .gz files are supported.

        colorspace -- Usually (when this is False), there must be n characters in the sequence and
        n quality values. When this is True, there must be n+1 characters in the sequence and n quality values.
        """
        if isinstance(file, str):
            file = xopen(file, "r")
        self.fp = file
        self.colorspace = colorspace
        self.twoheaders = False

    def __iter__(self):
        """
        Return tuples: (name, sequence, qualities).
        qualities is a string and it contains the unmodified, encoded qualities.
        """
        lengthdiff = 1 if self.colorspace else 0
        for i, line in enumerate(self.fp):
            if i % 4 == 0:
                if not line.startswith('@'):
                    raise FormatError("at line {}, expected a line starting with '+'".format(i+1))
                name = line.strip()[1:]
            elif i % 4 == 1:
                sequence = line.strip()
            elif i % 4 == 2:
                line = line.strip()
                if not line.startswith('+'):
                    raise FormatError("at line {}, expected a line starting with '+'".format(i+1))
                if len(line) > 1:
                    self.twoheaders = True
                    if not line[1:] == name:
                        raise FormatError(
                            "At line {}: Two sequence descriptions are given in "
                            "the FASTQ file, but they don't match "
                            "('{}' != '{}')".format(i+1, name, line.rstrip()[1:]))
            elif i % 4 == 3:
                qualities = line.rstrip("\n\r")
                if len(qualities) + lengthdiff != len(sequence):
                    raise ValueError("Length of quality sequence and length of read do not match (%d+%d!=%d)" % (len(qualities), lengthdiff, len(sequence)))
                id = name.split()[0]
                desc = " ".join(name.split()[1:])
                yield Sequence(id, desc, sequence, qualities)

    def __enter__(self):
        if self.fp is None:
            raise ValueError("I/O operation on closed FastqReader")
        return self

    def __exit__(self, *args):
        self.fp.close()


class SFFReader(object):
    """
    Reader for SFF files.
    """
    def __init__(self, file):
        """
        file is a filename or a file-like object.
        If file is a filename, then .gz files are supported.
        """
        if isinstance(file, str):
            file = xopen(file, "r")
        self.fp = file
        self.header_data = self.read_header(file)

    def read_bin_fragment(self, struct_def, fileh, offset=0, data=None, byte_padding=None):
        '''It reads a chunk of a binary file.
    
        You have to provide the struct, a file object, the offset (where to start
        reading).
        Also you can provide an optional dict that will be populated with the
        extracted data.
        If a byte_padding is given the number of bytes read will be a multiple of
        that number, adding the required pad at the end.
        It returns the number of bytes reads and the data dict.
        '''
        if data is None:
            data = {}
    
        #we read each item
        bytes_read = 0
        for item in struct_def:
            #we go to the place and read
            fileh.seek(offset + bytes_read)
            n_bytes = struct.calcsize(item[1])
            buffer = fileh.read(n_bytes)
            read = struct.unpack('>' + item[1], buffer)
            if len(read) == 1:
                read = read[0]
            data[item[0]] = read
            bytes_read += n_bytes
    
        #if there is byte_padding the bytes_to_read should be a multiple of the
        #byte_padding
        if byte_padding is not None:
            pad = byte_padding
            bytes_read = ((bytes_read + pad - 1) // pad) * pad
    
        return (bytes_read, data)

    def read_header(self, fileh):
        '''It reads the header from the sff file and returns a dict with the
        information'''
        #first we read the first part of the header
        head_struct = [
            ('magic_number', 'I'),
            ('version', 'cccc'),
            ('index_offset', 'Q'),
            ('index_length', 'I'),
            ('number_of_reads', 'I'),
            ('header_length', 'H'),
            ('key_length', 'H'),
            ('number_of_flows_per_read', 'H'),
            ('flowgram_format_code', 'B'),
        ]
        data = {}
        first_bytes, data = self.read_bin_fragment(struct_def=head_struct, fileh=fileh, offset=0, data=data)
        if data['magic_number'] != 779314790:
            raise RuntimeError('This file does not seems to be an sff file.')
        
        supported = ('\x00', '\x00', '\x00', '\x01')
        i = 0
        for item in data['version']:
            if data['version'][i] != supported[i]:
                raise RuntimeError('SFF version not supported. Please contact the author of the software.')
            i += 1
            
        #now that we know the number_of_flows_per_read and the key_length
        #we can read the second part of the header
        struct2 = [
            ('flow_chars', str(data['number_of_flows_per_read']) + 'c'),
            ('key_sequence', str(data['key_length']) + 'c')
        ]
        self.read_bin_fragment(struct_def=struct2, fileh=fileh, offset=first_bytes, data=data)
        return data

    def return_merged_clips(self, data):
        '''It returns the left and right positions to clip.'''
        def max(a, b):
            '''It returns the max of the two given numbers.
    
            It won't take into account the zero values.
            '''
            if not a and not b:
                return None
            if not a:
                return b
            if not b:
                return a
            if a >= b:
                return a
            else:
                return b
        def min(a, b):
            '''It returns the min of the two given numbers.
    
            It won't take into account the zero values.
            '''
            if not a and not b:
                return None
            if not a:
                return b
            if not b:
                return a
            if a <= b:
                return a
            else:
                return b
        left = max(data['clip_adapter_left'], data['clip_qual_left'])
        right = min(data['clip_adapter_right'], data['clip_qual_right'])
        #maybe both clips were zero
        if left is None:
            left = 1
        if right is None:
            right = data['number_of_bases']
        return left, right
    
    def clip_read(self, data):
        '''Given the data for one read it returns clipped seq and qual.'''
    
        qual = data['quality_scores']
        left, right = self.return_merged_clips(data)
        seq = data['bases']
        qual = data['quality_scores']
        new_seq = seq[left-1:right]
        new_qual = qual[left-1:right]
        new_name = data['name']
    
        return new_seq, new_qual, new_name

    def read_sequence(self, header, fileh, fposition):
        '''It reads one read from the sff file located at the fposition and
        returns a dict with the information.'''
        header_length = header['header_length']
        index_offset = header['index_offset']
        index_length = header['index_length']
    
        #the sequence struct
        read_header_1 = [
            ('read_header_length', 'H'),
            ('name_length', 'H'),
            ('number_of_bases', 'I'),
            ('clip_qual_left', 'H'),
            ('clip_qual_right', 'H'),
            ('clip_adapter_left', 'H'),
            ('clip_adapter_right', 'H'),
        ]
        def read_header_2(name_length):
            '''It returns the struct definition for the second part of the header'''
            return [('name', str(name_length) +'c')]
        def read_data(number_of_bases):
            '''It returns the struct definition for the read data section.'''
            #size = {'c': 1, 'B':1, 'H':2, 'I':4, 'Q':8}
            if header['flowgram_format_code'] == 1:
                flow_type = 'H'
            else:
                raise Error('file version not supported')
            number_of_bases = str(number_of_bases)
            return [
                ('flowgram_values', str(header['number_of_flows_per_read']) +
                                                                         flow_type),
                ('flow_index_per_base', number_of_bases + 'B'),
                ('bases', number_of_bases + 'c'),
                ('quality_scores', number_of_bases + 'B'),
            ]
    
        data = {}
        #we read the first part of the header
        bytes_read, data = self.read_bin_fragment(struct_def=read_header_1,
                                                  fileh=fileh, offset=fposition, data=data)
    
        self.read_bin_fragment(struct_def=read_header_2(data['name_length']),
                               fileh=fileh, offset=fposition + bytes_read, data=data)
        #we join the letters of the name
        data['name'] = ''.join(data['name'])
        offset = data['read_header_length']
        #we read the sequence and the quality
        read_data_st = read_data(data['number_of_bases'])
        bytes_read, data = self.read_bin_fragment(struct_def=read_data_st,
                                                  fileh=fileh, offset=fposition + offset,
                                                  data=data, byte_padding=8)
        #we join the bases
        data['bases'] = ''.join(data['bases'])
    
        # bugfix: 0 values for clips in SFF mean: not computed
        # see http://www.ncbi.nlm.nih.gov/Traces/trace.cgi?cmd=show&f=formats&m=doc&s=formats#sff
        # i.e.: right clip values must be set to length of sequences
        #       if that happens so that we can work with normal ranges
        if data['clip_qual_right'] == 0 :
            data['clip_qual_right'] = data['number_of_bases'];
        if data['clip_adapter_right'] == 0 :
            data['clip_adapter_right'] = data['number_of_bases'];
    
        # correct for the case the right clip is <= than the left clip
        # in this case, left clip is 0 are set to 0 (right clip == 0 means
        #  "whole sequence")
        if data['clip_qual_right'] <= data['clip_qual_left'] :
            data['clip_qual_right'] = 0
            data['clip_qual_left'] = 0
        if data['clip_adapter_right'] <= data['clip_adapter_left'] :
            data['clip_adapter_right'] = 0
            data['clip_adapter_left'] = 0
    
        #the clipping section follows the NCBI's guidelines Trace Archive RFC
        #http://www.ncbi.nlm.nih.gov/Traces/trace.cgi?cmd=show&f=rfc&m=doc&s=rfc
        #if there's no adapter clip: qual -> vector
        #else:  qual-> qual
        #       adapter -> vector
        if not data['clip_adapter_left']:
            data['clip_adapter_left'], data['clip_qual_left'] = data['clip_qual_left'], data['clip_adapter_left']
        if not data['clip_adapter_right']:
            data['clip_adapter_right'], data['clip_qual_right'] = data['clip_qual_right'], data['clip_adapter_right']
    
        data['bases'], data['quality_scores'], data['name'] = self.clip_read(data)
        data['number_of_bases']=len(data['bases'])
        data['clip_qual_right'] = data['number_of_bases']
        data['clip_adapter_right'] = data['number_of_bases']
        data['clip_qual_left'] = 0
        data['clip_adapter_left'] = 0
    
        return data['read_header_length'] + bytes_read, data

    def extract_sequences(self, fileh, header):
        '''It returns a generator with the data for each read.'''
        #now we can read all the sequences
        fposition = header['header_length']    #position in the file
        reads_read = 0
        while True:
            if fposition == header['index_offset']:
                #we have to skip the index section
                fposition += index_length
                continue
            else:
                bytes_read, seq_data = self.read_sequence(header=header, fileh=fileh, fposition=fposition)
                yield seq_data
                fposition += bytes_read
                reads_read += 1
                if reads_read >= header['number_of_reads']:
                    break

    def __iter__(self):
        """
        Return tuples: (name, desc, sequence, qualities).
        qualities is a string and it contains the unmodified, encoded qualities.
        """
        for seq_data in self.extract_sequences(fileh=self.fp, header=self.header_data):
            sequence, qualities, id = self.clip_read(seq_data)
            yield Sequence(id, "", sequence, qualities)
    
    def __enter__(self):
        if self.fp is None:
            raise ValueError("I/O operation on closed SFFReader")
        return self

    def __exit__(self, *args):
        self.fp.close()


def _quality_to_ascii(qualities, base=33):
    """
    Convert a list containing qualities given as integer to a string of
    ASCII-encoded qualities.

    base -- ASCII code of quality zero (sensible values are 33 and 64).

    >>> _quality_to_ascii([17, 4, 29, 18])
    '2%>3'
    """
    qualities = ''.join(chr(q+base) for q in qualities)
    return qualities


class FastaQualReader(object):
    """
    Reader for reads that are stored in .(CS)FASTA and .QUAL files.
    """
    def __init__(self, fastafile, qualfile, colorspace=False, qual2ascii=False, splitqual=False):
        """
        fastafile and qualfile are filenames file-like objects.
        If file is a filename, then .gz files are supported.

        colorspace -- Usually (when this is False), there must be n characters in the sequence and
        n quality values. When this is True, there must be n+1 characters in the sequence and n quality values.
        """
        self.fastareader = FastaReader(fastafile)
        self.qualreader = FastaReader(qualfile, keep_linebreaks=True)
        self.colorspace = colorspace
        self.qual2ascii = qual2ascii
        self.splitqual = splitqual

    def __iter__(self):
        """
        Return tuples: (name, sequence, qualities).
        qualities is a string and it contains the qualities encoded as ascii(qual+33).
        """
        lengthdiff = 1 if self.colorspace else 0
        for fastaread, qualread in zip(self.fastareader, self.qualreader):
            if self.qual2ascii:
                qualities = _quality_to_ascii(list(map(int, qualread.sequence.split())))
            elif self.splitqual:
                qualities = qualread.sequence.split()
            else:
                qualities = qualread.sequence
            assert fastaread.name == qualread.name
            qualitiest = qualities.split()
            
            id = fastaread.name.split()[0]
            desc = " ".join(fastaread.name.split()[1:])
            
            if len(qualitiest) + lengthdiff != len(fastaread.sequence):
                raise ValueError("Length of quality sequence and length of read do not match (%s: %d+%d!=%d)" % (
                    id, len(qualitiest), lengthdiff, len(fastaread.sequence)))

            yield Sequence(id, desc, fastaread.sequence, qualities)

    def __enter__(self):
        if self.fastafile is None:
            raise ValueError("I/O operation on closed FastaQualReader")
        return self

    def __exit__(self, *args):
        self.fastareader.close()
        self.qualreader.close()
        

def writefasta(f, seqlist, linelength=None):
    """
    Print out a FASTA-formatted file from data given in seqlist.

    seqlist -- iterable over (name, sequence) tuples
    f -- output file
    linelength -- If this isn't None, wrap lines after linelength characters.
    """
    if linelength is not None:
        for id, desc, seq, qual in seqlist:
            f.write('>')
            header = id + ' ' + desc
            if desc == '':
                header = id
            f.write(header)
            f.write('\n')
            for i in range(0, len(seq), linelength):
                f.write(seq[i:i+linelength])
                f.write('\n')
    else:
        for id, desc, seq, qual in seqlist:
            header = id + ' ' + desc
            if desc == '':
                header = id
            f.write('>%s\n%s\n' % (header, seq))

def writequalities(f, seqlist, linelength=None):
    """
    Print out a FASTA-formatted file from data given in seqlist.

    seqlist -- iterable over (name, sequence) tuples
    f -- output file
    linelength -- If this isn't None, wrap lines after linelength characters.
    """
    if linelength is not None:
        for id, desc, seq, qual in seqlist:
            if isinstance(qual, str):
                qual = qual.split()
            f.write('>')
            header = id + ' ' + desc
            if desc == '':
                header = id
            f.write(header)
            f.write('\n')
            clinelenght = 0
            cline = ""
            for val in qual:
                clinelenght += len(val)
                if clinelenght == linelength-1:
                    f.write(cline + val)
                    f.write('\n')
                    clinelenght = 0
                    cline = ""
                elif clinelenght + 1 == linelength-1:
                    f.write(cline + val)
                    f.write('\n')
                    clinelenght = 0
                    cline = ""
                elif clinelenght > linelength-1:
                    f.write(cline.rstrip())
                    f.write('\n')
                    clinelenght = len(val) + 1
                    cline = val + " "
                else:
                    cline += val + " "
                    clinelenght += 1
            if cline != "":
                f.write(cline.rstrip())
                f.write('\n')
    else:
        for id, desc, seq, qual in seqlist:
            header = id + ' ' + desc
            if desc == '':
                header = id
            f.write('>%s\n%s\n' % (header, qual))

def writefastq(f, seqlist, twoheaders=False):
    """
    seqlist must contain (description, sequence, qualities) tuples

    If twoheaders is True, the sequence name (description) is also written
    after the "+" character.
    """
    for id, desc, sequence, qualities in seqlist:
        header = id + ' ' + desc
        if desc == '':
            header = id
        tmp = header if twoheaders else ''
        f.write('@%s\n%s\n+%s\n%s\n' % (header, sequence, tmp, qualities))