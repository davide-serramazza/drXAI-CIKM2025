import numpy as np
from tsCaptum.explainers import Feature_Ablation, Shapley_Value_Sampling
from windowshap import MyWindowSHAP
import timeit
from utils.channels_extraction import _detect_knee_point
import torch

def extract_selection_absFirst(attribution):
	"""
	function to extract relevant time points/channels out of a saliency maps
	:param attribution:		the saliency map where to extract relevant attribution
	:return: 				selected channels
	"""

	attribution = np.abs(attribution)
	chs_relevance = np.average(np.average(attribution , axis=-1),axis=0)

	ordered_scores_idx = lambda x : ( np.flip(np.sort(x).tolist()) , np.flip(np.argsort(x)).tolist() )
	ordered_relevance, ordered_idx = ordered_scores_idx(chs_relevance)
	knee_selection = _detect_knee_point(ordered_relevance,ordered_idx )

	return knee_selection

def extract_selection_attribution(attribution, abs):
	"""
	function to extract relevant time points/channels out of a saliency maps
	:param attribution:		the saliency map where to extract relevant attribution
	:param abs: 			whether to use the absolut value i.e. one knee_cut or not i.e. two different knee_cuts
	:return: 				selected channels
	"""
	chs_relevance = np.average(np.average(attribution , axis=-1),axis=0)

	ordered_scores_idx = lambda x : ( np.flip(np.sort(x)) , np.flip(np.argsort(x)) )

	if abs:
		# have only on knee cut based on the channel relevance score's absolute value
		chs_relevance =  np.abs(chs_relevance)
		ordered_relevance, ordered_idx = ordered_scores_idx(chs_relevance)
		knee_selection = _detect_knee_point(ordered_relevance,ordered_idx )
	else:
		# otherwise compute two difference ones and take their union
		ordered_relevance, ordered_idx = ordered_scores_idx(chs_relevance)
		negatives = np.where(ordered_relevance<0)[0]
		if negatives.shape==(0,):
			# no negative values
			knee_selection = []
		else:
			negative_start_idx = negatives[0]

			pos_knee_selection = _detect_knee_point(
				ordered_relevance[:negative_start_idx],
				ordered_idx[:negative_start_idx]
			)

			neg_knee_selection = _detect_knee_point(
				np.flip(np.abs(ordered_relevance[negative_start_idx:])),
				np.flip(ordered_idx[negative_start_idx:]) )


			print( "pos:",len(pos_knee_selection),"out of", len(ordered_relevance[:negative_start_idx]) ,
				   "neg:",len(neg_knee_selection),"out of", len(ordered_relevance[negative_start_idx:]))

			knee_selection = np.concatenate( ( pos_knee_selection , neg_knee_selection) ).tolist()

	return knee_selection


def get_AI_selections(saliency_map_dict, selection_dict, accuracies, info):
	# TODO find a better name
	# TODO move  these functions somewhere else?

	for k in saliency_map_dict.keys():
		if k=='labels_map':
			continue
		if k=='accuracy':
			accuracies[info[1:]] = saliency_map_dict[k]
		elif k.startswith('selected_channels'):
			k_name = k.replace('selected_channels_','')
			model, explainer = info.split("_")[1] , "_".join( info.split("_")[2:] )
			if saliency_map_dict[k]!=[]:
				selection_dict[model]["_".join(( explainer,k_name) )] = saliency_map_dict[k]


		elif type(saliency_map_dict[k])==dict :
			get_AI_selections(
				saliency_map_dict[k],selection_dict,accuracies,
				info+"_"+str(k))

	return selection_dict, accuracies


def add_mostAccurate(all_selections,initial_accuracies):
	# get most accurate
	most_accurate_model = max(initial_accuracies, key=lambda model: initial_accuracies[model])
	AI_selections =	(set( all_selections[most_accurate_model].keys()).
						difference(set(['elbow_pairwise', 'elbow_sum'])))	# take out the two elbows

	best_model_AI_selections = [(selection,all_selections[most_accurate_model][selection]) for selection in AI_selections]

	# add this selection to other models
	other_models = set(initial_accuracies.keys()).difference(set([most_accurate_model]))
	for model in other_models:
		for (name,selection) in best_model_AI_selections:
			all_selections[model]["most_accurate_model_"+name] =selection

	return all_selections

def get_elbow_selections(current_data,elbows):
	return {
		'elbow_pairwise' : elbows[current_data]['Pairwise'] ,
		'elbow_sum' : elbows[current_data]['Sum']
	}

###################################	explainers #############################################

def windowSHAP_selection(model, X_explain, background_data, return_saliency=True, to_terminate=None):

	# so far hard coded 0 baseline
	# TODO do i need to_terminate param ???
	# TODO do I need return_saliency param???
	n_instances, n_channels ,n_time_points = X_explain.shape
	w_len =  np.ceil(n_time_points/3).astype(int).item()	; stride = np.ceil(n_time_points/5).astype(int).item()
	saliency_maps = []


	# explain instance by instance
	start_time = timeit.default_timer()
	for i in range(n_instances):
		print(i, "out of",n_instances)
		current_saliency_map = MyWindowSHAP(model.predict_proba, test_data = X_explain[i:i+1],
				background_data = background_data,window_len = w_len, stride = stride, method = 'sliding').shap_values()
		saliency_maps.append(current_saliency_map)
		# is termination flag has been set by the main thread break the loo[
		#if to_terminate.is_set():
		#	current_experiment['Window_SHAP']['timeout'] = True
		#	print("WindowSHAP has run out of time")
		#	break
	tot_time = timeit.default_timer() - start_time

	saliency_maps = np.concatenate( saliency_maps )

	selections = []
	for absolute in [True, False]:
		selection = extract_selection_attribution(saliency_maps, abs=absolute)
		selections.append( selection )
	selections.append( extract_selection_absFirst(saliency_maps))

	# return accordingly to parameters
	to_return = (selections, saliency_maps,tot_time) if return_saliency else (selections,tot_time)

	return to_return

def tsCaptum_selection(model, X, y, batch_size,background, explainer_name, return_saliency):

	# TODO do I need return_saliency param???

	# check explainer to be used
	if explainer_name=='Feature_Ablation':
		algo = Feature_Ablation
	elif explainer_name=='Shapley_Value_Sampling':
		algo = Shapley_Value_Sampling
	else:
		raise ValueError("only Feature_Ablation and Shapley_Value_Sampling are allowed")

	explainer = algo(model)

	start_time = timeit.default_timer()
	#TODO n_segment is hard coded
	saliency_map = explainer.explain(samples=X, labels=y, n_segments=10,normalise=False,
											baseline=background,batch_size=batch_size)
	tot_time = timeit.default_timer() - start_time

	#TODO should we change this??
	selections = []
	for absolute in [True, False]:
		selection = extract_selection_attribution(saliency_map, abs=absolute)
		selections.append( selection )
	selections.append( extract_selection_absFirst(saliency_map))

	# return accordingly to parameters
	to_return = (selections, saliency_map, tot_time) if return_saliency else (selections,tot_time)

	return to_return



