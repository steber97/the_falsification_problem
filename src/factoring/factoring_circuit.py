from typing import List, Tuple, Mapping
from sympy import isprime
import math
import time

from factoring.circuitSAT import CircuitSAT
from factoring.utils import randprime


class FactoringCircuit(CircuitSAT):
    """
    SAT circuit resembling the factorization of x.
    It implements the "school method" multiplier circuit of two
    factors p, q (represented as a binary number), and returns true
    if p * q = x.
    """
    def __init__(self, x: int):
        super().__init__()
        # input gates with the two factors.
        # p is longer (sizeof(x)-1) whereas q has size sizeof(x)/2
        # sizeof(x) is in bits. This is to take into account both 
        # x = y * 2 (sizeof(p) = sizeof(x) - 1) and 
        # x = sqrt(x) * sqrt(x) (sizeof(p) = sizeof(q) = sizeof(x)/2).
        # p and q are the input gates that represent the prime factors.
        self.p: List[CircuitSAT.Gate] = []
        self.q: List[CircuitSAT.Gate] = []

        self._factoringToSat(x)

    def _factoringToSat(self, x: int) -> None:
        """
        Builds a boolean circuit that implements a "school method" binary multiplier circuit.
        This circuit has as inputs the bit representation of p, q, the two (prime) factors.
        It proceeds performing len(q) sums of p * q[i], shifted by i steps to the left.

        @param x: the circuit, given in input the binary representation of two numbers p and q, returns
            true iff p * q = x. 
        """
        x_bits = self._convertIntToBinary(x)
        n = len(x_bits)
        self.n = n  # Tentative.
        # Only factor number n given by a * b, with |a| = |b| = |n|/2
        self.p = [CircuitSAT.Gate("input", i, []) for i in range(n//2 if (n % 2) == 0 else (n//2) + 1)]
        self.q = [CircuitSAT.Gate("input", len(self.p) + i, []) for i in range(n//2 if (n % 2) == 0 else (n//2) + 1)]
        assert (len(self.p) >= len(self.q)) and (len(self.q) > 0)
        for gate in self.p:
            self.addGate(gate)
        for gate in self.q:
            self.addGate(gate)
        
        nextgate = len(self.p) + len(self.q) + 1

        falsegate = CircuitSAT.Gate("F", nextgate, [])
        self.addGate(falsegate)
        nextgate += 1

        prev_res = [CircuitSAT.Gate("and", nextgate + i, [self.p[i], self.q[0]]) for i in range(len(self.p))]
        for g in prev_res:
            self.addGate(g)
        nextgate += len(self.p)
        output_inputs = []
        for rep in range(1, len(self.q)):
            y = [CircuitSAT.Gate("and", nextgate + i, [self.q[rep], self.p[i]]) for i in range(len(self.p))]
            for gate in y:
                self.addGate(gate)
            nextgate += len(self.p)

            # Avoid summing all the false gates, just append the beginning of prev_res 
            # to the output of the sum.
            if (len(prev_res[len(self.p):]) > len(y)):
                prev_res_tmp, nextgate = self._reduceSumToSAT(prev_res[rep:], y, nextgate)
            else:
                prev_res_tmp, nextgate = self._reduceSumToSAT(y, prev_res[rep:], nextgate)
            
            # The first :rep bits of prev_res would be summed to false gates. 
            # Just send them to the next iter unchanged.
            prev_res = prev_res[:rep] + prev_res_tmp
            
            if len(prev_res) > n:
                # Ensure that n+1 onward bits are zero
                if len(prev_res) > n+1:
                    self.addGate(CircuitSAT.Gate("or", nextgate, [prev_res[i] for i in range(n, len(prev_res))]))
                    self.addGate(CircuitSAT.Gate("not", nextgate + 1, [self.map_id_to_gate[nextgate]]))
                    output_inputs.append(self.map_id_to_gate[nextgate + 1])
                    nextgate += 2
                else:
                    self.addGate(CircuitSAT.Gate("not", nextgate, [prev_res[n]]))
                    output_inputs.append(self.map_id_to_gate[nextgate])
                    nextgate += 1
                prev_res = prev_res[:n]
            assert len(prev_res) <= n

        assert len(prev_res) == n
        
        for bit, res in zip(x_bits, prev_res):
            self.addGate(CircuitSAT.Gate("T" if bit else "F", nextgate, []))
            self.addGate(CircuitSAT.Gate("iff", nextgate+1, [self.map_id_to_gate[nextgate], res]))
            output_inputs.append(self.map_id_to_gate[nextgate+1])
            nextgate += 2
        # Ensure that final product is x!
        self.addGate(CircuitSAT.Gate("and", nextgate, output_inputs), output=True)        

    def _reduceSumToSAT(self, x: List[CircuitSAT.Gate], y: List[CircuitSAT.Gate], nextgate: int) -> Tuple[List[CircuitSAT.Gate], int]:
        """
        Creates a binary addition circuit, that sums x and y.
        The addition is implemented with a xor gate, with additional and/or gates for the remainer.

        @param x: first binary number.
        @param y: second binary number.
        @param nextgate: next available gate_id.
        @returns result: List of gates added to the circuit.
        @returns nextgate: new next available gate_id.
        """
        result = []
        remainder = []
        assert len(x) >= len(y)
        for i in range(len(x)):
            if i < len(y):
                result.append(CircuitSAT.Gate("xor", nextgate, [x[i], y[i]] + ([remainder[i-1]] if i > 0 else [])))
                self.addGate(result[-1])
                nextgate += 1
                rem1 = CircuitSAT.Gate("and", nextgate, [x[i], y[i]])
                self.addGate(rem1)
                nextgate += 1
                if i > 0:
                    rem2 = CircuitSAT.Gate("and", nextgate, [x[i], remainder[i-1]])
                    rem3 = CircuitSAT.Gate("and", nextgate+1, [y[i], remainder[i-1]])
                    nextgate += 2
                    self.addGate(rem2)
                    self.addGate(rem3)
                    remainder.append(CircuitSAT.Gate("or", nextgate, inputs=[rem1, rem2, rem3]))
                    self.addGate(remainder[-1])
                    nextgate += 1
                else:
                    remainder.append(rem1)
            else:
                result.append(CircuitSAT.Gate("xor", nextgate, [x[i], remainder[i-1]]))
                nextgate += 1
                remainder.append(CircuitSAT.Gate("and", nextgate, [x[i], remainder[i-1]]))
                nextgate += 1
                self.addGate(result[-1])
                self.addGate(remainder[-1])
        result.append(remainder[-1])
        return result, nextgate
    
    def _convertBitstringToInt(self, bitstring: List[bool]) -> int:
        """
        Given the bit representation of a binary number,
        return its int representation.
        It is the inverse of _convertIntToBinary().

        @param bitstring: the binary representation of a number. The least significant bit comes first.
        @returns: the int representation of bitstring.
        """
        res = 0
        for i, x in enumerate(bitstring):
            res += (2**i) * x
        return res
    
    def _convertIntToBinary(self, n: int) -> List[bool]:
        """
        Given an int, return a list of boolean values that
        correspond to its binary representation.
        The least significant bit comes first.
        It is the inverse of _convertBitstringToInt

        @param n: the integer
        @returns: the binary representation of the integer n, the least significant bit coming first.
        """
        size = math.floor(math.log2(n))
        rem = n
        result = []
        for j in range(size, -1, -1):
            if rem >= (2 ** j):
                result.append(1)
                rem -= (2**j)
            else:
                result.append(0)
        assert rem == 0
        return [i for i in reversed(result)]

    def getFactorsFromCnfAssignment(self, model: List[int], map: Mapping[int, int]) -> Tuple[int, int]:
        """
        Given a model for the cnf assignment:

        @param model: list of integers (id of variables), with +- sign embedding
                      the variable assignment. e.g. x1=T, x2=F, .. = [1, -2, ...]
        @param map: a map, mapping gates of the original SAT circuit to variables in the CNF
                with the same truth value.
        @returns p, q the two integer factors.S
        """
        cnf_model = {}
        for x in model:
            id = x if x > 0 else - x
            cnf_model[id] = x > 0
        p_bits = []
        q_bits = []
        for in1 in self.p:
            p_bits.append(cnf_model[map[in1.id]])
        for in2 in self.q:
            q_bits.append(cnf_model[map[in2.id]])
        p_int = self._convertBitstringToInt(p_bits)
        q_int = self._convertBitstringToInt(q_bits)
        return p_int, q_int
