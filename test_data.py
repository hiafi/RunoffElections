import csv
import itertools
import os
import random 
import string
from datetime import datetime
from math import factorial
import simplejson as json
import unittest2 as unittest

file_inorder_100 = "test_data/inorder_100.csv"
file_random_100 = "test_data/random_100.csv"
file_51_majority = "test_data/51_majority.csv"
file_single_elimination = "test_data/single_elimination.csv"
file_multi_elmination = "test_data/multi_elimination.csv"
file_all_elmination = "test_data/all_elimination.csv"
file_tie = "test_data/tie.csv"
file_random_real = "test_data/random_sim.csv"
file_conc = "test_data/conc.csv"
file_branch1 = "test_data/branch1.csv"

# pre-calcutation permutation so it's not done on the fly
# should the number of canidates in the fixture change
permutation = list(itertools.permutations([i for i in range(1, 7)], 6))

class voter(object):
    def __init__(self, possible_votes, fixtures='fixtures/canidates.json'):
        self.first_name  = self.gen_fake_name()
        self.last_name  = self.gen_fake_name()
        self.email = self.first_name + '.' + self.last_name + '@students.wwu.edu'
        self.region = ''
        self.department = ''
        self.ballot = {}
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        self.assign_votes(possible_votes, fixtures)
    
    def gen_fake_name(self):
        name  = ''.join([random.choice(string.ascii_lowercase) for i in range(random.randint(5, 20))])
        name[0].upper()
        return name

    def assign_votes(self, possible_votes, fixtures):
        """
        Assigns the votes to the voters ballot given the range of
        possible_votes
        """ 
        if not isinstance(possible_votes, list):
            raise TypeError("possible_votes must be a list")

        fh = open(fixtures, 'r')
        canidates = json.load(fh)

        for k, v in canidates.iteritems():
            random_index = random.randint(0, len(possible_votes) - 1)
            self.ballot[k] = dict(zip(v, possible_votes[random_index]))
        fh.close()

def voter_generator(count, vote_range):
    for i in range(0, count):
        yield voter(vote_range)

class ElectionsTestCases(object):
    def case_test(self, outfile='output.csv'):
        """
        Generates one voter and writes them to the file
        """
        vote_range = [permutation[0]] #cast to a list
        voters = list(voter_generator(1, vote_range))
        return self.write_results(voters, outfile)

    def case_inorder_100(self, outfile='output.csv'):
        """
        Generates 100 voters and writes them to the file
        """
        vote_range = [permutation[0]] # cast to a list
        voters = list(voter_generator(100, vote_range)) 
        return self.write_results(voters, outfile)
    
    def case_test_51_majority(self, outfile='output.csv'):
        """
        Generates voters and writes them to the file
        """
        vote_range = permutation[0:120]
        voters = list(voter_generator(51, vote_range))

        vote_range = permutation[120:720]
        voters.extend(list(voter_generator(49, vote_range)))
        return self.write_results(voters, outfile)
    
    def case_tie(self, outfile='output.csv'):
        """
        Generates 100 voters and writes them to the file
        """
        # First candiate in fixture list gets 50% of the votes
        vote_range = [p for p in permutation if p[0] == 1]
        voters = list(voter_generator(50, vote_range)) 

        vote_range = [p for p in permutation if p[1] == 1]
        voters.extend(list(voter_generator(50, vote_range)))
        
        return self.write_results(voters, outfile)
    
    def case_single_elimination(self, outfile='output.csv'):
        """
        Generates 100 voters and writes them to the file
        """
        # First candiate in fixture list gets 45% of the votes
        vote_range = permutation[0:120]
        voters = list(voter_generator(45, vote_range)) 

        # Second candidate gets %20
        vote_range = [p for p in permutation if p[1] == 1]
        voters.extend(list(voter_generator(20, vote_range)))

        # Third canidate gets %14
        vote_range = [p for p in permutation if p[2] == 1]
        voters.extend(list(voter_generator(14, vote_range)))

        # Forth canidate gets %8
        vote_range = [p for p in permutation if p[3] == 1]
        voters.extend(list(voter_generator(8, vote_range)))

        # Fifth gets another %7
        vote_range = [p for p in permutation if p[4] == 1]
        voters.extend(list(voter_generator(7, vote_range)))

        # Elimated canidate gets %6, but these voters also voted
        # for the first canidate as their second choice
        vote_range = [p for p in permutation if p[5] == 1 and p[0] == 2 ]
        voters.extend(list(voter_generator(6, vote_range)))

        return self.write_results(voters, outfile)
    
    def case_multiple_elimination(self, outfile='output.csv'):
        """
        Eliminate 3 canidates
        """
        # First candiate in fixture list gets 35% of the votes
        vote_range = permutation[0:120]
        voters = list(voter_generator(35, vote_range)) 

        # Second candidate gets %21
        vote_range = [p for p in permutation if p[1] == 1]
        voters.extend(list(voter_generator(21, vote_range)))

        # Third canidate gets %19
        vote_range = [p for p in permutation if p[2] == 1]
        voters.extend(list(voter_generator(19, vote_range)))

        # Forth canidate gets %12
        vote_range = [p for p in permutation if p[3] == 1 and p[0] == 2]
        voters.extend(list(voter_generator(12, vote_range)))

        # Fifth gets another %7
        vote_range = [p for p in permutation if p[4] == 1 and p[0] == 2]
        voters.extend(list(voter_generator(7, vote_range)))

        # Elimated canidate gets %6, but these voters also voted
        # for the first canidate as their second choice
        vote_range = [p for p in permutation if p[5] == 1 and p[0] == 2 ]
        voters.extend(list(voter_generator(6, vote_range)))

        return self.write_results(voters, outfile)
    
    def case_concurrent_elimination(self, outfile='output.csv'):
        """
        Eliminate 3 canidates
        """
        # First candiate in fixture list gets 35% of the votes
        vote_range = permutation[0:120]
        voters = list(voter_generator(40, vote_range)) 

        # Second candidate gets %21
        vote_range = [p for p in permutation if p[1] == 1]
        voters.extend(list(voter_generator(19, vote_range)))

        # Third canidate gets %19
        vote_range = [p for p in permutation if p[2] == 1]
        voters.extend(list(voter_generator(16, vote_range)))

        # Forth canidate gets %12
        vote_range = [p for p in permutation if p[3] == 1 and p[0] == 2]
        voters.extend(list(voter_generator(14, vote_range)))

        # Fifth gets another %7
        vote_range = [p for p in permutation if p[4] == 1 and p[0] == 2]
        voters.extend(list(voter_generator(6, vote_range)))

        # Elimated canidate gets %6, but these voters also voted
        # for the first canidate as their second choice
        vote_range = [p for p in permutation if p[5] == 1 and p[0] == 2 ]
        voters.extend(list(voter_generator(5, vote_range)))

        return self.write_results(voters, outfile)
    
    def case_branch(self, outfile='output.csv'):
        """
        low level tie to demonstraight branching
        """
        vote_range = [p for p in permutation if p[0] == 1 and p[1] == 2]
        voters = list(voter_generator(30, vote_range)) 
        
        # Second candidate gets %30
        vote_range = [p for p in permutation if p[1] == 1 and p[0] == 2]
        voters.extend(list(voter_generator(30, vote_range)))

        # Third canidate gets %20
        vote_range = [p for p in permutation if p[2] == 1 and p[0] == 2 and p[1] == 3]
        voters.extend(list(voter_generator(20, vote_range)))

        # Forth canidate gets %20
        vote_range = [p for p in permutation if p[3] == 1 and p[2] == 2 and p[0] == 3]
        voters.extend(list(voter_generator(20, vote_range)))
        
        return self.write_results(voters, outfile)
    
    def case_random_data(self, outfile='output.csv'):
        vote_range = permutation[0:720]
        voters = list(voter_generator(14000, vote_range)) 
        return self.write_results(voters, outfile)

    def case_rand_permutation(self, outfile='output.csv'):
        """
        Generates 100 voters with random voting habits and
        writes them to the file
        """
        vote_range = permutation
        voters = [voter(vote_range) for i in range(0, 100)]
        return self.write_results(voters, outfile)

    def write_results(self, voters=[], outfile='output.csv'):
        if not isinstance(voters, list) and voters:
            raise TypeError("Voters must be a list of voter objects")

        if os.path.isfile(outfile):
            os.remove(outfile)

        fh = open(outfile, 'wb')
        out = csv.writer(fh, dialect=csv.excel)

        tester = []
        for voter in voters:
            for position, canidates in voter.ballot.iteritems():
                for canidate, vote in canidates.iteritems():
                    row = [ voter.last_name[0:8], voter.first_name, voter.last_name,
                            voter.email, voter.region, voter.department,
                            position, canidate, str(), str(vote), voter.date ]
                    tester.append(row)
                    out.writerow(row)
        fh.close()
        return tester

class TestTestCase(unittest.TestCase):
    def setUp(self):
        self.test = ElectionsTestCases()
        self.fixture = open('fixtures/canidates.json')
        self.canidates = json.load(self.fixture)

    def tearDown(self):
        self.fixture.close()

    def verify_written_data(self, written_data, outfile):
        output = open(outfile, 'rb')
        test_file = csv.reader(output, dialect=csv.excel)
        for n, row in enumerate(test_file):
            self.assertListEqual(written_data[n], row) 
        output.close()

    def test_case_single(self):
        """
        test_case_test
        Test to see if when we have 1 person, we have all of our data
        """
        self.test.case_test()
        self.output = open('output.csv', 'rb')
        self.test_file = csv.reader(self.output, dialect=csv.excel)
        for row in self.test_file:
            posistion = row[6]
            vote = int(row[9]) - 1
            self.assertEqual(self.canidates[posistion][vote], row[7])

    def test_inorder_100(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_inorder_100
        self.test.case_inorder_100(outfile)
        self.output = open(outfile, 'rb')
        self.test_file = csv.reader(self.output, dialect=csv.excel)
        for row in self.test_file:
            posistion = row[6]
            vote = int(row[9]) - 1
            self.assertEqual(self.canidates[posistion][vote], row[7])
            
    def test_51_majority(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_51_majority
        written_data = self.test.case_test_51_majority(outfile)
        self.verify_written_data(written_data, outfile)

    def test_random_permutation(self):
        """  
        test_case_randome_permutation
        Test to see if when we have random data, we still have everything there
        """
        outfile = file_random_100
        written_data = self.test.case_rand_permutation(outfile)
        self.verify_written_data(written_data, outfile)
            
    def test_single_elimination(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_single_elimination
        written_data = self.test.case_single_elimination(outfile)
        self.verify_written_data(written_data, outfile)
        
    def test_multi_elimination(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_multi_elmination
        written_data = self.test.case_multiple_elimination(outfile)
        self.verify_written_data(written_data, outfile)
        
    def test_concurrent_elimination(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_conc
        written_data = self.test.case_concurrent_elimination(outfile)
        self.verify_written_data(written_data, outfile)
        
    def test_branch(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_branch1
        written_data = self.test.case_branch(outfile)
        self.verify_written_data(written_data, outfile)
        
    def test_tie(self):
        """
        test_case_test_100
        Test to see if when we have 100 people, our data matches up
        """
        outfile = file_tie
        written_data = self.test.case_tie(outfile)
        self.verify_written_data(written_data, outfile)
        
    def test_rand_data(self):
        """Generates true random data"""
        outfile = file_random_real
        written_data = self.test.case_random_data(outfile)
        self.verify_written_data(written_data, outfile)
        
        

#    def test_cast_random_perm_rand_null(self):
#        """Test to see if when we have random data, we still have everything there"""
#        self.test.case_test_rand_perm_rand_nulls()
#        for n, row in enumerate(self.test_file):
#            posistion = row[5]
#            self.assertEqual(self.canidates[posistion][n % 6], row[6])


if __name__ == '__main__':
   unittest.main()
