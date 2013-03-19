import sys

from languageModelManager import LanguageModelManager as lmm

class StatelessFeatures(object):
    __slots__ = "tmFVec", "wp", "glue"
    
    def __init__(self, tmFeats, wp_val, glue_val = 0.0):
        self.tmFVec = tmFeats[:]
        self.wp = wp_val
        self.glue = glue_val

    @classmethod
    def copySLFeat(cls, other):
        return StatelessFeatures(other.tmFVec, other.wp, other.glue)

    def aggregFeatScore(self, other):
        # Aggregate the feature values of the stateless feats of antecendts with that of inference item
        indx = 0
        for tm_f_val in other.tmFVec:
            self.tmFVec[indx] += tm_f_val
            indx += 1

        self.wp += other.wp
        self.glue += other.glue

    def stringifyMembers(self):
        return ' '.join( [str("%g" % x) for x in self.tmFVec] ), str("%g" % self.wp), str("%g" % self.glue)


class StatefulFeatures(object):
    
    lmInitLst = []
    __slots__ = "lmFVec", "lm_heu", "comp_score"

    def __init__(self, lmFeats, sful_score = 0.0, lm_heu = 0.0):
        self.lmFVec = lmFeats[:]
        self.comp_score = sful_score
        self.lm_heu = lm_heu

    @classmethod
    def initNew(cls, lm_heu):
        return StatefulFeatures(StatefulFeatures.lmInitLst, 0.0, lm_heu)

    @classmethod
    def setLMInitLst(cls, tot_lm_feats):
        StatefulFeatures.lmInitLst = [0.0 for x in xrange(tot_lm_feats)]

    @classmethod
    def copySFFeat(cls, other):
        return StatefulFeatures(other.lmFVec, other.comp_score)

    @classmethod
    def replicateSFFeat(cls, other):
        return StatefulFeatures(other.lmFVec, other.comp_score, other.lm_heu)

    def getLMHeu(self):
        return self.lm_heu

    def aggregSFScore(self, anteSfLst):
        '''Aggregates the stateful score of inf item by summing it with that of ante items'''
        for ante_sf_obj in anteSfLst:
            self.comp_score += ante_sf_obj.comp_score

        return self.comp_score        # return stateful features score

    def getStateScore(self):
        return self.comp_score + self.lm_heu

    def helperScore(self, newConsItems, is_last_cell):
        '''Helper function for computing stateful scores (recomputes lm_heu)'''
        (frag_lm_score, lm_comp_heu) = lmm.helperLM(newConsItems, is_last_cell, self.lmFVec)
        self.comp_score += frag_lm_score
        self.lm_heu = lm_comp_heu
        return frag_lm_score + self.lm_heu

    def aggregFeatScore(self, ante_sf_obj):
        '''Aggregates the stateful features for a given sf_obj pertaining to a final hypothesis'''

        indx = 0
        for ante_fval in ante_sf_obj.lmFVec:
            self.lmFVec[indx] += ante_fval
            indx += 1

    def stringifyMembers(self, cand_hyp):
        return lmm.adjustUNKLMScore(cand_hyp, self.lmFVec)