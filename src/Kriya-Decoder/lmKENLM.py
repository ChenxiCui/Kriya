## @author baskaran

import os
import sys

kenlm_swig_wrapper = os.environ.get("NGRAM_SWIG_KENLM")
if ( kenlm_swig_wrapper is None ):
    sys.stderr.write("Error: Environment variable NGRAM_SWIG_KENLM is not set. Exiting!!\n")
    sys.exit(1)
sys.path.insert(1, kenlm_swig_wrapper)
import settings
from kenlm import *

class KENLangModel(object):
    '''Language Model class for KENLM'''

    log_normalizer = 0.434294                       # Normalizer to convert the log-10 value (of KenLM) to natural log

    __slots__ = "LM", "lm_order", "elider"

    def __init__(self, lm_order, lmFile, elider_str):
        '''Import the KENLM wrapper module and initialize LM'''

        self.LM = None
        self.lm_order = lm_order
        self.elider = elider_str
        self.loadLM(lmFile)

    def __del__(self):
        '''Deletes the LM variable'''

        deleteLM(self.LM)

    def loadLM(self, lmFile):
        '''Function for loading the LM'''

        self.LM = readLM(lmFile)             # Read lmFile into LM variable

    ## Functions for querying the LM
    ## Define them as classmethods so that they can be called directly with class
    def queryLM(self, phr, phr_len):
        '''Score a target phrase with the Language Model and return natural log'''

        return getNGramProb(self.LM, phr, phr_len) / KENLangModel.log_normalizer

    def queryLMlog10(self, phr, phr_len):
        '''Score a target phrase with the Language Model and return base-10 log'''

        return getNGramProb(self.LM, phr, phr_len)

    def calcUNKLMScore(self, sent):
        '''Calculate the LM score contribution by UNK (OOV) words'''

        return scoreUNK(self.LM, sent) / KENLangModel.log_normalizer

    def printState(self, state):
        """  Printing the KENLM state object (for debugging) """

        return getHistory(self.LM, state)

    def getLMState(self, r_edge_phr):
        '''Get the forward looking state for current target hypothesis'''
        r_lm_state = getEmptyState(self.LM)
        dummy_prob = getNGramProb(self.LM, r_edge_phr, getEmptyState(self.LM), r_lm_state)    
        return r_lm_state

    def scoremGrams(self, phrStateTupLst):
        '''Score all the complete m-grams in a given consequent item'''

        ## Score the complete n-gram phraes
        span_indx = 0
        lm_temp = 0.0
        for (mgram_phr, lm_hist) in phrStateTupLst:
            if lm_hist is None:
                lm_temp += getNGramProb(self.LM, mgram_phr, self.lm_order, 'true')
            else:
                lm_temp += getNGramProb(self.LM, mgram_phr, lm_hist, 'true')
            span_indx += 1

        return lm_temp / KENLangModel.log_normalizer

    def getLMHeuCost(self, cons_item):
        """ Compute Heuristic LM score for a given consequent item (by merging one or two antecedents).

            Heuristic LM score is calculated for m-1 words in the beginning and end
            of the candidate. The sentence-boundary markers (<s> and </s>) are first
            appended to the candidate and the heuristic scores are then computed
            separately for three cases, i) no boundary, ii) only left boundary and
            iii) only right boundary. The best (max) score from among the three are
            then returned as the LM heuristic score.
        """

        ## Compute LM heuristic score for the first m-1 words ##
        # Hypothesis is an S-rule (is_S_rule is True)
        if (cons_item.eTgtLst[0] == "<s>"):
            return getLMHeuProb(self.LM, ' '.join(cons_item.eTgtLst[1:self.lm_order-1]), 1, 0) / KENLangModel.log_normalizer

        # Hypothesis is *not* an S-rule (is_S_rule is False)
        if (cons_item.e_len < self.lm_order): l_edge = ' '.join(cons_item.eTgtLst)
        else: l_edge = ' '.join(cons_item.eTgtLst[0:self.lm_order-1])

        left_edge_heu = getLeftEdgeHeu(self.LM, l_edge, 0)
        left_edge_heu_sbeg = getLeftEdgeHeu(self.LM, l_edge, 1)
        lmHeuLst = [left_edge_heu, left_edge_heu_sbeg, left_edge_heu]

        # Compute LM heuristic score for the last m-1 words
        if cons_item.eTgtLst[-1] != "</s>":
            if cons_item.e_len < self.lm_order: r_edge = l_edge
            else: r_edge = ' '.join(cons_item.eTgtLst[1-self.lm_order:])    # Simpification of: -(self.lm_order - 1)
            right_edge_heu = getRightEdgeHeu(self.LM, r_edge, 0)
            right_edge_heu_send = getRightEdgeHeu(self.LM, r_edge, 1)
            lmHeuLst[0] += right_edge_heu
            lmHeuLst[1] += right_edge_heu
            lmHeuLst[2] += right_edge_heu_send

        return max(lmHeuLst) / KENLangModel.log_normalizer                  # Return the max value of LM heu
