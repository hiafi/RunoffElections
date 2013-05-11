import csv
import sys
import ordereddict
import xlrd
from math import ceil
from os import urandom
from collections import defaultdict
from hashlib import sha256
import unittest2 as unittest
import simplejson as json
from copy import deepcopy
from couchdbkit import Document, IntegerProperty, ListProperty, DictProperty
from couchdbkit import StringProperty

# Test data imports
from test_data import file_inorder_100, file_random_100
from test_data import file_51_majority, file_tie
from test_data import file_single_elimination, file_multi_elmination
from test_data import file_random_real, file_conc, file_branch1

class voter(object):
    def __init__(self, **kwargs):
        self.set_properties(kwargs)
        self.ballot = defaultdict(dict) 

    def set_vote(self, vote):
        if not isinstance(vote, list) and len(vote) != 4:
            raise TypeError(""" The Vote must be repestented as a four item
            list: [Posistion, Canidate, Write-in, Ranking] """)

        if vote[2]:
            self.ballot[vote[0]][vote[2]] = int(vote[3])
        else:
            self.ballot[vote[0]][vote[1]] = int(vote[3])

    def set_properties(self, kwargs):
        """
        Sets the basic string properities of the voter
        """
        valid_properties = ['user_name', 'last_name', 'first_name',
                'email', 'region', 'department', 'date']

        for k, v in kwargs.iteritems():
            if k in valid_properties:
                if isinstance(v, basestring):
                    setattr(self, k, v)
                else:
                    raise TypeError("{0} must be a string".format(k))
                
class CouchDBResult(Document):
    position = StringProperty()
    iteration = IntegerProperty()
    result = DictProperty()
    children = ListProperty()
    path = ListProperty()
    eliminated = StringProperty()
    
                
class Result(object):
    """
    Tree like object for calculating votes
    """
    def __init__(self, iteration, results, name=""):
        self.name = name
        self.iteration = iteration
        self.result = results
        self.children = []
        
    def write_document_tree(self, database, position, parent_result = {}, path=[]):
        doc = CouchDBResult()
        doc._id = sha256(self.__repr__()).hexdigest()
        doc.iteration = self.iteration
        doc.result = self.result
        doc.position = u'{0}'.format(position)
        doc.path = path
        doc.path.append(doc._id)
        if self.iteration != 0:
            for person in self.result.iterkeys():
                if self.result[person] == 0 and parent_result[person]>0:
                    doc.eliminated = person
        children = []
        for child in self.children:
            children.append(child.write_document_tree(database, position, self.result, doc.path))
        doc.children = children
        database.save_doc(doc) #save the document here
        return doc._id

class Canidate(object):
    """
    What people are voting on
    """
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.votes_stack = []
        #self.eliminated = False
   
    @property
    def eliminated(self):
        if len(self.votes_stack) == 0:
            return True
        else:
            return False

    @property
    def votes(self):
        if not self.eliminated:
            return len(self.votes_stack)
        else:
            return 0 

    def __cmp__(self, other):
        if self.votes > other.votes:
            return 1
        elif self.votes < other.votes:
            return -1
        else:
            return 0

    def __repr__(self):
        return "<{0} for {1}: {2} (stack: {3})>".format(self.name,
                self.position, self.votes, len(self.votes_stack))
    
class ASElectionResults(object):
    salt = ""
    def __init__(self, result_file=None):
        if not isinstance(result_file, basestring):
            raise TypeError("Results must be a string")
        self.result_file = result_file
        self.voter_dict= {}
        self.canidate_dict = defaultdict(dict)
        self.tabulated_passes = {}

    @staticmethod
    def get_salt():
        if ASElectionResults.salt == "":
            ASElectionResults.salt = urandom(16).encode('hex')
        return ASElectionResults.salt

    def tabulate_results(self, out_file="output.json"):
        self.read_results_file()
        self.initial_tabulation()
        res = self.idfs_results(out_file)
        return res
    
    def results_tree_to_dict(self, results, results_dict):
        """
        returns a dictonary tree like thing of the results
        """
        if len(results.children) == 0:
            results_dict[results.iteration] = results.result
            return results_dict
        elif len(results.children) > 1:
            results_dict[results.iteration] = results.result
            branch_dict = {}
            for child in results.children:
                branch_dict[child.name] = {}
                self.results_tree_to_dict(child, branch_dict[child.name])
            results_dict[results.iteration+1] = branch_dict
            return results_dict
        else:
            results_dict[results.iteration] = results.result
            return self.results_tree_to_dict(results.children[0], results_dict)

         
    def read_results_file(self):
        """
        Read the results and instanciate the voter and 
        canidate objects
        """
        file_type = self.result_file.split('.')[-1]

        if file_type == 'csv':
            self.read_csv()
        elif file_type == 'xls':
            self.read_xls()

    def read_xls(self):
        votes_file = xlrd.open_workbook(self.result_file)
        sheet = votes_file.sheet_by_index(0)
        row_v = sheet.cell_value

        salt = ASElectionResults.get_salt()

        for row in range(sheet.nrows):
            user_name = row_v(rowx=row, colx=0)
            first_name = row_v(rowx=row, colx=1)
            last_name = row_v(rowx=row, colx=2)
            email = row_v(rowx=row, colx=3)
            position = row_v(rowx=row, colx=6)
            vote = [ row_v(rowx=row, colx=i) for i in range(6, 11)]

            # Test if this vote is for a write-in canidate
            if row_v(rowx=row, colx=8) !=  '':
                canidate = row_v(rowx=row, colx=8)
            elif row_v(rowx=row, colx=7): 
                # If there isn't a write-in there will be a canidate, but
                # test anyway
                canidate = row_v(rowx=row, colx=7)
            self.assign_vote(salt, user_name, first_name, last_name, email, position, canidate, vote)

    def read_csv(self):
        votes_file = open(self.result_file, 'rb')
        test_file = csv.reader(votes_file, dialect=csv.excel)

        salt = ASElectionResults.get_salt()

        # Each row in the CSV represents a vote by a voter
        for row in test_file:
            user_name = row[0]
            first_name = row[1]
            last_name = row[2]
            email = row[3]
            position = row[6]
            vote = row[6:10]

            # Test if this vote is for a write-in canidate. Un-needed test, but doing 
            # it anyway.
            if row[8] !=  '':
                canidate = row[8]
            elif row[7]: 
                # If there isn't a write-in there will be a canidate, but
                # test anyway
                canidate = row[7]
            self.assign_vote(salt, user_name, first_name, last_name, email, position, canidate, vote)

    def assign_vote(self, salt, user_name, first_name, last_name, email, position, canidate, vote):
        """
        Assign a vote to a canidate
        """
        # Set the canidate in the candidate_dict 
        if not canidate in self.canidate_dict[position]:
            self.canidate_dict[position][canidate] = Canidate(canidate,  position)
        
        # Need a (somewhat) safe unique id for the voter
        voter_id = sha256(user_name + first_name + last_name + email + salt).hexdigest()
        
        # Create the voter and add the vote to his/her ballot
        if not voter_id in self.voter_dict:
    		v = voter()
    		self.voter_dict[voter_id] = v
        
        self.voter_dict[voter_id].set_vote(vote)
        return self.voter_dict
        
    def initial_tabulation(self):
        """ 
        Read the results and instanciate voter objects from 
        the rows in the file
        """
        # The initial pass to get the recursion going, set the voters to their
        # initial ballot and then start counting and eliminating canidates
        for voter in self.voter_dict.itervalues():
            for position in voter.ballot.iterkeys():
                for canidate in voter.ballot[position].iterkeys():
                    if voter.ballot[position][canidate] == 1:
                        self.canidate_dict[position][canidate].votes_stack.append(voter)

    def idfs_results(self, file="output.json"):
        """
        Write the results to a file
        """
        end_res = {}
        self.t_passes = {}
        for position in self.canidate_dict.iterkeys():
            end_res[position] = self.count_votes(position, 0, self.canidate_dict[position])

        if file!=None:
            res = {}
            for position in end_res.iterkeys():
                output = self.results_tree_to_dict(end_res[position], {})
                wfile = open("{0}_{1}.{2}".format(file.split(".")[0], position, file.split(".")[1]), 'w')
                wfile.write(json.dumps(output))
                wfile.close()
                res[position] = output
            return end_res
        else:
            return end_res
        
    def count_votes(self, position, iteration, canidates):
        """
        Do the actual counting of the votes, basically, find out the loser/s, eliminate them
         by removing all of their voters and moving to the voters next choice, if there is a tie to who gets eliminated,
         we branch causing some parallel dimension stuff!
        """
        sorted_canidates = sorted(canidates.values())
        sorted_canidates.reverse() # put the leader at index 0 
        total_votes = sum([ c.votes for c in sorted_canidates])

        #record the pass
        pass_results = {}
        for canidate in canidates.itervalues():
            pass_results[canidate.name] = canidate.votes
        iter_results = Result(iteration, pass_results)
        
        #Prune the eliminated canidates from the list
        pruned_sorted_canidates = [ canidate for canidate in sorted_canidates if not canidate.eliminated ]
        
        # Determine if there is a winner
        if pruned_sorted_canidates[0].votes < int((ceil(total_votes * .5) + 1)):
            eliminate_list = []
            i = -1
            if pruned_sorted_canidates[i].votes == pruned_sorted_canidates[i-1].votes:
                eliminate_list.extend([pruned_sorted_canidates[i], pruned_sorted_canidates[i-1]])
                children = self.branch_votes(position, iteration+1, canidates, eliminate_list)
                for child in children:
                    iter_results.children.append(child)
            else:
                eliminate_list.append(pruned_sorted_canidates[i])

                while (pruned_sorted_canidates[i].votes + pruned_sorted_canidates[i - 1].votes) < pruned_sorted_canidates[i - 2].votes:
                    eliminate_list.append(pruned_sorted_canidates[i - 1])
                    i -= 1
                self.eliminate_canidate(position, canidates, eliminate_list)
                iter_results.children.append(self.count_votes(position, iteration+1, canidates))

        return iter_results
    
    def branch_votes(self, position, iteration, canidates, eliminate_list):
        """
        Parallel Dimensions!
        branch on tie, allowing the vote master to determine the correct winner / loser
        """
        canidate_branch = {} #we will copy our canidates
        ret_children = [] #here are the children we return
        for removed, branch in enumerate(eliminate_list):
            canidate_branch[branch.name] = deepcopy(canidates)
            modified_eliminate_list = deepcopy(eliminate_list)
            del modified_eliminate_list[removed]     
            canidate_branch[branch.name] = self.eliminate_canidate(position, canidate_branch[branch.name], modified_eliminate_list)
            result = self.count_votes(position, iteration, canidate_branch[branch.name])
            result.name = branch.name
            ret_children.append(result)
        return ret_children
    
    def eliminate_canidate(self, position, canidates, eliminate_list):
        """
        Remove the canidate and shift their votes
        """
        for canidate in eliminate_list:
            stack = canidates[canidate.name].votes_stack
            while stack:
                voter = stack.pop()
                placed = False
                exhausted = False
                while not placed and not exhausted:
                    exhausted = True
                    for key in voter.ballot[position].iterkeys():
                        voter.ballot[position][key] -= 1
                        if voter.ballot[position][key] == 1 and canidates[key].eliminated == False:
                            canidates[key].votes_stack.append(voter)
                            placed = True
                            exhausted = False
                        if exhausted and voter.ballot[position][key] > 0:
                            exhausted = False
        return canidates

#==============================================
#                    Unit tests               #
#==============================================

class ElectionResultsTest(unittest.TestCase):
    def setUp(self):
        self.canidate_fixture = open('fixtures/canidates.json')
        self.canidates = json.load(self.canidate_fixture)

    def test_100_inorder_majority(self):      
        self.maxDiff = None
        res = ASElectionResults(file_inorder_100)
        res.tabulate_results("output/100_inorder.json")
        results = {}
        
        results_fixture = open('fixtures/inorder_100_results.json')
        expected_results = json.load(results_fixture)
        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/100_inorder_{0}.json'.format(position)))
        
        self.assertDictEqual(results, expected_results)

    def test_51_majority(self):      
        res = ASElectionResults(file_51_majority)
        res.tabulate_results("output/51_inorder.json")
        results = {}
        
        results_fixture = open('fixtures/51_majority_results.json')
        expected_results = json.load(results_fixture)
        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/51_inorder_{0}.json'.format(position)))

        for position in expected_results.iterkeys():
            for canidate in expected_results[position]['0'].iterkeys():
                self.assertEqual(results[position]['0'][canidate], expected_results[position]['0'][canidate])

    def test_single_elimination(self):
        res = ASElectionResults(file_single_elimination)
        res.tabulate_results("output/100_sing.json")
        results = {}
        
        results_fixture = open('fixtures/single_elimination_results.json')
        expected_results = json.load(results_fixture)
        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/100_sing_{0}.json'.format(position)))
        self.assertDictEqual(results, expected_results)
        
    def test_multi_elimination(self):
        res = ASElectionResults(file_multi_elmination)
        res.tabulate_results("output/100_multi.json")
        results = {}
        results_fixture = open('fixtures/multi_elimination_results.json')
        expected_results = json.load(results_fixture)
        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/100_multi_{0}.json'.format(position)))
        self.assertDictEqual(results, expected_results)
        
    def test_tie(self):
        res = ASElectionResults(file_tie)
        res.tabulate_results("output/tie.json")
        results = {}
        
        results_fixture = open('fixtures/tie.json')
        expected_results = json.load(results_fixture)

        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/tie_{0}.json'.format(position)))

        self.assertDictEqual(results, expected_results)
        
    def test_conc(self):
        res = ASElectionResults(file_conc)
        res.tabulate_results("output/conc.json")
        results = {}
        
        results_fixture = open('fixtures/conc.json')
        expected_results = json.load(results_fixture)

        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/conc_{0}.json'.format(position)))
        
        self.assertDictEqual(results, expected_results)
        
    def test_branch(self):
        res = ASElectionResults(file_branch1)
        test = res.tabulate_results("output/branch1.json")
        results = {}
        results_fixture = open('fixtures/branch1.json')
        expected_results = json.load(results_fixture)

        for position in expected_results.iterkeys():
            results[position] = json.load(open('output/branch1_{0}.json'.format(position)))
        
        self.assertDictEqual(results, expected_results)

if __name__ == "__main__":
    unittest.main()
