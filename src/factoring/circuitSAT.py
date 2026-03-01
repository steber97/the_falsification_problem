from typing import List, Mapping, Tuple, Self, Optional, Dict

from factoring.cnfSAT import CnfSAT


class CircuitSAT:
    """
    Class that implements an instance of CircuitSAT.
    Gates need to be aranged in a DAG fashion.
    Input gates (of the circuit) should have fan-in 0.
    There can be only one output gate (the output value of the circuit).
    """

    class Gate:
        """
        Simple class that implements a logical gate.
        Only a few types have been implemented.
        you should imagine the gate as:
        
        in_1 ----|
        in_2 ----|
        in_3 ----|--> gate ->  
        ...  
        in_n ----|

        Hence it is not necessary that the fan-in is 2.
        Notice also that some gates have 1 fan in (not)
        or 0 fan-in (input, T, F).
        """
        def __init__(self, type: str, id: int, inputs: List[Self]):
            """
            @param type: any of or, and, not, xor, iff, T, F, input, output
            @param id: the integer id of the gate. It needs to be unique!
            @param inputs: the input gates of the current gate. 
                According to the type, the number of input gates might differ.
            """
            # Implemented types.
            self.types = [
                "or", 'and', 'not', 'xor', 'iff',
                'T', 'F', 'input', 'output'
            ]
            self.type: str = type
            self.inputs: List[Self] = inputs  # list of input gates
            self.id: int = id  # The id must be unique!
            self._check_consistency()
        
        def _check_consistency(self):
            """
            For every type, check that the number of inputs is coherent with the gate.
            """
            if self.type == "or":
                pass
            elif self.type == "and":
                pass
            elif self.type == "not":
                assert len(self.inputs) == 1
            elif self.type == "xor":
                pass
            elif self.type == "iff":
                assert len(self.inputs) == 2
            elif self.type == "T":
                assert len(self.inputs) == 0
            elif self.type == "F":
                assert len(self.inputs) == 0
            elif self.type == "input":
                assert len(self.inputs) == 0
            elif self.type == "output":
                pass
            else:
                raise ValueError('{} is not a supported type for gates'.format(self.type))
        
        def __str__(self) -> str:
            return "({}, {}, {})".format(self.id, self.type, [x.id for x in self.inputs])
        
    def __init__(self):
        # Use method addGate to add gates. This preserves topological order.
        self.gates: List[CircuitSAT.Gate] = []             
        self.map_id_to_gate: Dict[int, CircuitSAT.Gate] = {}  # Map int->Gate
        self.inputs: List[CircuitSAT.Gate] = []            # List input gates
        self.output: Optional[CircuitSAT.Gate] = None                # Output gate

    def addGate(self, gate: Gate, output=False):
        """
        Gates must be added in topological order.
        Input gates should probably come first, although it is not necessary.

        @param gate:   gate to add to the circuit.
        @param output: boolean value, True if the gate added is the output
                       of the circuit. There can only be 1 output gate.
        """
        # assert you already added all inputs. (i.e. enforce topological order).
        for input in gate.inputs:
            assert input.id in self.map_id_to_gate
        # Assert that the new id is unique!
        assert gate.id not in self.map_id_to_gate
        self.gates.append(gate)
        self.map_id_to_gate[gate.id] = gate
        if gate.type == "input":
            self.inputs.append(gate)
        if output:
            # There can be only one output.
            assert self.output == None
            self.output = gate

    def get_output_gate(self) -> Gate:
        """
        Wrapper to get the output gate (and not an option for it).
        When using get_output(), you must be sure that the output gate has been
        initialized to some. Otherwise, it will raise a RuntimeError.

        @returns: the output gate.
        """
        if self.output is None:
            raise RuntimeError("At this point, the output gate cannot be None!")
        return self.output

    def eval(self, input_bits: Mapping[int, bool]) -> bool:
        """
        input_bits should map t/f assignments of all input bits.
        Simply evaluate the circuit on the given input bits.

        @param input_bits: map input_id -> truth assignment.
                           Notice that all input bits must be set!
        @returns
            - the truth value of the circuit evaluated with the given input bits.
        """
        for i in input_bits:
            # Assert you specified only input gates' assignments.
            assert i in self.map_id_to_gate and self.map_id_to_gate[i].type == 'input'
        # Assert you specified all input gates' assignments.
        assert len(self.inputs) == len(input_bits)
        assignments: Mapping[int, bool] = {}
        for i in input_bits:
            assignments[i] = input_bits[i]
        return self._eval_rec(self.get_output_gate(), assignments)

    def _eval_rec(self, gate: Gate, assignments: Mapping[int, bool]) -> bool:
        """
        Recursively evaluate all gates using memoization:
        if you don't know the value of the input gates, recurse on them.

        @param gate: current gate to evaluate
        @param assignments: map gate_id -> truth assignment built so far.
        @returns if the gate is true or not. Also updates assignment map.
        """
        # memoization
        if gate.id in assignments:
            return assignments[gate.id]
        else:
            # recursively compute all gates, using memoization
            inputs = [self._eval_rec(self.map_id_to_gate[x.id], assignments) for x in gate.inputs]
            type = gate.type
            if type == "or":
                return sum(inputs) >= 1
            elif type == "and":
                return sum(inputs) == len(inputs)
            elif type == "T":
                return True
            elif type == "F":
                return False
            elif type == "xor":
                return (sum(inputs) % 2) == 1
            elif type == "iff":
                return (sum(inputs) == 0) or (sum(inputs) == len(inputs))
            elif type == "not":
                return not inputs[0]
            else:
                raise ValueError # cannot admit other types!

    def _reduceGateToCnf(self, 
                         gate: Gate, 
                         nextvar: int, 
                         map_gate_output_to_cnf_var: Mapping[int, int]
                         ) -> Tuple[List[List[int]], int, int]:
        """
        Reduce a single gate to CNF. This is a wrapper for the specific type reduction.

        @param gate:
        @param nextvar: the next index that can be used as a fresh new variable.
        @param map_gate_output_to_cnf_var: gate_id -> var_id in the CNF with equal truth value
        @returns:
            - clauses to add to cnf
            - new value for nextvar
            - variable index in cnf with same truth value as input gate.
        """
        assert gate.id in self.map_id_to_gate
        for input in gate.inputs:
            # In case this exception happens, variables are not specified in topological order.
            assert input.id in map_gate_output_to_cnf_var
        if gate.type == "or":
            return self._reduceOrGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "and":
            return self._reduceAndGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "not":
            return self._reduceNotGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "xor":
            return self._reduceXorGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "iff":
            return self._reduceIffGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "T":
            return self._reduceTGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "F":
            return self._reduceFGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        elif gate.type == "input":
            return self._reduceInputGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
        else:
            raise ValueError("wrong gate type!")
    
    def _reduceOrGateToCnf(self, 
                           gate: Gate, 
                           nextvar: int, 
                           map_gate_output_to_cnf_var: Mapping[int, int]
                           ) -> Tuple[List[List[int]], int, int]:
        """
        Create a list of CNF clauses with equal meaning to the input gate.
        Assume the gate is a or b ->
        Create a series of cnf clauses s.t. variable x respects 
        x iff (a or b)
        i.e. (not(x) or a or b) and (not(a) or x) and (not(b) or x)
        Concatenate such clauses if the gate has fan-in > 2.
        gate: a or b or c ...
        (x_2 iff (x_1 or c)) and (x_1 iff a or b) ...
        (not(x_2) or x_1 or c) and (not(x_1) or x_2) and (not(c) or x_2) and ...
        In the above example, the variable index with the same truth value as 
        the input gate would be x_2.
        
        @params : as _reduceGateToCnf
        @returns : as _reduceGateToCnf
        """
        assert len(gate.inputs) >= 2 and gate.type == 'or'
        a = map_gate_output_to_cnf_var[gate.inputs[0].id]
        clauses = []
        for i in range(1, len(gate.inputs)):
            b = map_gate_output_to_cnf_var[gate.inputs[i].id]
            clauses += [[a, b, -nextvar], 
                        [nextvar, -a],
                        [nextvar, -b]]
            a = nextvar
            nextvar += 1
        return clauses, nextvar, a
    
    def _reduceAndGateToCnf(self, 
                            gate: Gate,
                            nextvar: int, 
                            map_gate_output_to_cnf_var: Mapping[int, int]
                            ) -> Tuple[List[List[int]], int, int]:
        """
        x iff (a and b)
        (not(x) or a) and (not(x) or b) and (x or not(b) or not(a))
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) >= 2 and gate.type == "and"
        a = map_gate_output_to_cnf_var[gate.inputs[0].id]
        clauses = []
        for i in range(1, len(gate.inputs)):
            b = map_gate_output_to_cnf_var[gate.inputs[i].id]
            clauses += [[-nextvar, a],
                        [-nextvar, b], 
                        [nextvar, -a, -b]]
            a = nextvar
            nextvar += 1
        return clauses, nextvar, a

    def _reduceNotGateToCnf(self, 
                            gate: Gate, 
                            nextvar: int, 
                            map_gate_output_to_cnf_var: Mapping[int, int]
                            ) -> Tuple[List[List[int]], int, int]:
        """
        x iff not(a)
        (x or a) and (not(x) or not(a))
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) == 1 and gate.type == "not"
        a = map_gate_output_to_cnf_var[gate.inputs[0].id]
        return [[a, nextvar], [-a, -nextvar]], nextvar + 1, nextvar

    def _reduceXorGateToCnf(self, 
                            gate: Gate, 
                            nextvar: int, 
                            map_gate_output_to_cnf_var: Mapping[int, int]
                            ) -> Tuple[List[List[int]], int, int]:
        """
        x iff a xor b
        (a or b or not(x)) and (not(a) or not(b) or not(x)) and (not(a) or b or x) and (a or not(b) or x)
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) >= 2 and gate.type == "xor"
        a = map_gate_output_to_cnf_var[gate.inputs[0].id]
        clauses = []
        for i in range(1, len(gate.inputs)):
            b = map_gate_output_to_cnf_var[gate.inputs[i].id]
            clauses += [[a, b, -nextvar],
                        [-a, -b, -nextvar],
                        [a, -b, nextvar], 
                        [-a, b, nextvar]]
            a = nextvar
            nextvar += 1
        return clauses, nextvar, a

    def _reduceIffGateToCnf(self, 
                            gate: Gate, 
                            nextvar: int, 
                            map_gate_output_to_cnf_var: Mapping[int, int]
                            ) -> Tuple[List[List[int]], int, int]:
        """
        x iff (a iff b)
        (a or b or x) and (not(a) or not(b) or x) and (a or not(b) or not(x)) and (not(a) or b or not(x))
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) == 2 and gate.type == "iff"
        a = map_gate_output_to_cnf_var[gate.inputs[0].id]
        b = map_gate_output_to_cnf_var[gate.inputs[1].id]
        clauses = [[a, b, nextvar],
                   [-a, -b, nextvar],
                   [a, -b, -nextvar], 
                   [-a, b, -nextvar]]
        return clauses, nextvar + 1, nextvar

    def _reduceTGateToCnf(self, 
                          gate: Gate, 
                          nextvar: int, 
                          map_gate_output_to_cnf_var: Mapping[int, int]
                          ) -> Tuple[List[List[int]], int, int]:
        """
        x = true:
        (a or x) and (not(a) or x)
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) == 0 and gate.type == "T"
        a = nextvar
        nextvar += 1
        return [[a, nextvar], [-a, nextvar]], nextvar+1, nextvar

    def _reduceFGateToCnf(self, 
                          gate: Gate, 
                          nextvar: int, 
                          map_gate_output_to_cnf_var: Mapping[int, int]
                          ) -> Tuple[List[List[int]], int, int]:
        """
        x = false:
        (a or not(x)) and (not(a) or not(x))
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert len(gate.inputs) == 0 and gate.type == "F"
        a = nextvar
        nextvar += 1
        return [[a, -nextvar], [-a, -nextvar]], nextvar+1, nextvar
        

    def _reduceInputGateToCnf(self, 
                              gate: Gate, 
                              nextvar: int, 
                              map_gate_output_to_cnf_var: Mapping[int, int]
                              ) -> Tuple[List[List[int]], int, int]:
        """
        Basically do nothing.
        See comments of _reduceOrGateToCnf for a more precise description.
        """
        assert gate.type == "input"
        return [], nextvar + 1, nextvar

    def _gatesTopoSorted(self) -> bool:
        """
        Checks if the gates are topologically sorted.
        Namely, for every gate, check that its input gates appear
        before it.
        """
        gates_ids = set()
        for gate in self.gates:
            gate: CircuitSAT.Gate
            for input in gate.inputs:
                if input.id not in gates_ids:
                    # Some input hasn't appeared yet.
                    return False
            gates_ids.add(gate.id)
        return True

    def toCNF(self) -> Tuple[CnfSAT, Mapping[int, int]]:
        """
        Converts the SAT formula to CNF.
        Reduction is O(1)-factor larger than the number of wires in the circuit.
        
        @returns
            - a cnf formula with the same sat value.
            - a map, mapping gates of the original SAT circuit to variables in the CNF
                with the same truth value. Particularly useful to know which ones are the
                input/output variables of the CNF.
        """
        nextvar = 1  # Variables start from 1!
        clauses = []
        # maps gate id to output variable of cnf with same truth value as the gate.
        map_gate_output_to_cnf_var: Mapping[int, int] = {}
        assert self._gatesTopoSorted()
        for gate in self.gates:  # These must be given in topological order.
            gate: CircuitSAT.Gate
            new_clauses, nextvar, var = self._reduceGateToCnf(gate, nextvar, map_gate_output_to_cnf_var)
            map_gate_output_to_cnf_var[gate.id] = var  # var in cnf with same truth value of the gate.
            clauses += new_clauses
        return CnfSAT(clauses), map_gate_output_to_cnf_var

    def __str__(self) -> str:   
        result = ""
        for gate in reversed(self.gates):
            result += " {}".format(gate)
        return result
