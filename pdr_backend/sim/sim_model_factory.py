
@enforce_types
class SimModelFactory:    
    def __init__(self, aimodel_ss: AimodelSS):
        self.aimodel_ss = aimodel_ss
      
    def do_build(self, prev_model: Optional[SimModel], test_i: int) -> bool:
        """Update/train model?"""
        return prev_model is None or \
            test_i % self.aimodel_ss.train_every_n_epochs == 0
      
    def build(self, sim_model_data: SimModelData) -> SimModel:
        d = sim_model_data
        model_f = AimodelFactory(self.aimodel_ss)
        
        model_UP = model_f.build(
            d.UP.X_train,
            d.UP.ytrue_train,
            None,
            None,
        )
        
        model_DOWN = model_f.build(
            d.DOWN.X_train,
            d.DOWN.ytrue_train,
            None,
            None,
        )
        
        sim_model = SimModel(model_UP, model_DOWN)
        return sim_model
