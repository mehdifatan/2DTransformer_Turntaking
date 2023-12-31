import torch
import pandas as pd
import pickle
import os
import numpy as np
from transformer.batch import subsequent_mask
from Models4 import Transformer
import torch.nn.functional as F
import torch.nn as nn
import datetime
import gc
import matplotlib.pyplot as plt
from Prepare_data import prepare_multiclass_data_from_preprocessed_hdf5
from torch.nn import MultiheadAttention 

from vocalist.models.transformer_encoder import TransformerEncoder

#from multihead_attention import MultiheadAttention

from Layers import EncoderLayer, DecoderLayer
from Embed import Embedder, PositionalEncoder
from Sublayers import Norm
import copy
from new_layer import RBF_MLP
from new_layer import gaussian


import argparse

import gc



parser = argparse.ArgumentParser(description='EgoCom Turn-Taking Prediction')
parser.add_argument('--future-pred', default=3, type=int,
                    help='Specifies on how long in the future we are going'
                         'to predict. Default use of predicting 1 sec in the'
                         'future. Other values to be used are 1,3,5,10')
parser.add_argument('--history-sec', default=4, type=int,
                    help='Specifies on how many seconds of the past we are'
                         'using as a history feature. Default value is 4sec'
                         'but also can be used 4,10,30.')
parser.add_argument('--include-prior', default=None, type=str,
                    help='By default (None) this will run train both a model'
                         'with a prior and a model without a prior.'
                         'Set to "true" to include the label of the current'
                         'speaker when predicting who will be speaking in the'
                         'the future. Set to "false" to not include prior label'
                         'information. You can think of this as a prior on'
                         'the person speaking, since the person who will be'
                         'speaking is highly related to the person who is'
                         'currently speaking.')
parser.add_argument('--sequence-len', default=10, type=int,
                    help='Determine the sequence length of the transformer.'
                         'Could be any integer and has a default vale 10.')



class NoamOpt:
	"Optim wrapper that implements rate."
	def __init__(self, model_size, factor, warmup, optimizer):
		self.optimizer = optimizer
		self._step = 0
		self.warmup = warmup
		self.factor = factor
		self.model_size = model_size
		self._rate = 0

	def step(self):
		"Update parameters and rate"
		self._step += 1
		rate = self.rate()
		for p in self.optimizer.param_groups:
			p['lr'] = rate
		self._rate = rate
		self.optimizer.step()

	def rate(self, step = None):
		"Implement `lrate` above"
		if step is None:
			step = self._step
		return self.factor * \
			(self.model_size ** (-0.5) *
			min(step ** (-0.5), step * self.warmup ** (-1.5)))



def tuple_of_tensors_to_tensor(tuple_of_tensors):
    return  torch.stack(list(tuple_of_tensors), dim=0)



class MyEnsemble(nn.Module):
    def __init__(self, model1, model2, model3, model4, model5, model6, model1t, model2t, model3t, model1_2, model2_1, model1_3, model3_1, model2_3, model3_2, model1_1, model2_2, model3_3, att_layer, att_layer2):
        super(MyEnsemble, self).__init__()
        
        if include_prior==True:

            self.emb1=nn.Linear(N1+3, 512).float().to(device)
            self.emb2=nn.Linear(N2+3, 512).float().to(device)
            self.emb3=nn.Linear(N3+3, 512).float().to(device)

        else:

            self.emb1=nn.Linear(N1, 512).float().to(device)
            self.emb2=nn.Linear(N2, 512).float().to(device)
            self.emb3=nn.Linear(N3, 512).float().to(device)


        self.model1 = model1
        self.model2 = model2
        self.model3 = model3
        self.model4 = model4
        self.model5 = model5
        self.model6 = model6

        # they are not used
        self.model1t = model1t
        self.model2t = model2t
        self.model3t = model3t

        self.model1_2 = model1_2
        self.model2_1 = model2_1
        self.model1_3 = model1_3
        self.model3_1 = model3_1
        self.model2_3 = model2_3
        self.model3_2 = model3_2

        # they are not used
        self.model1_1 = model1_1
        self.model2_2 = model2_2
        self.model3_3 = model3_3


        self.att_layer = att_layer
        self.att_layer2 = att_layer2
               
        self.linear = nn.Linear(1024,4).float().to(device)

        self.lineart1 = nn.Linear(4,512).float().to(device)
        self.lineart2 = nn.Linear(4,512).float().to(device)
        self.lineart3 = nn.Linear(4,512).float().to(device)

    
    def forward(self, src1, src2, src3, src_att1, src_att2, src_att3, target_input, trg_att):


        # ASK MEHDI: this is to have all the source with the same feat dim (512)
        pred1 = self.emb1(src1)
        pred2 = self.emb2(src2)
        pred3 = self.emb3(src3)
        
        # ASK MEHDI: target input is the scope in the image

        #predt1 = self.lineart1(target_input)
        #predt2 = self.lineart1(target_input)
        #predt3 = self.lineart1(target_input)
        # TRY THIS #
        predt1 = self.lineart1(target_input)



        pred1 = self.model1(pred1)
        pred2 = self.model2(pred2)
        pred3 = self.model3(pred3)
        
        
        
        pred1 = self.model4(pred1,pred1,predt1)
        pred2 = self.model5(pred2,pred2,predt1)
        pred3 = self.model6(pred3,pred3,predt1)
        
        
        # predt scope
        # predt1 = self.model4(predt1)
        # predt2 = self.model4(predt2)
        # predt3 = self.model4(predt3)
        
        # TRY THIS
        #predt1 = self.model4(predt1)
        '''
        pred1 =  torch.cat((pred1, predt1), 2)
        pred2 =  torch.cat((pred2, predt2), 2)
        pred3 =  torch.cat((pred3, predt3), 2)
        '''
        
        #pred1 =  torch.cat((pred1, predt1), 2)
        #pred2 =  torch.cat((pred2, predt1), 2)
        #pred3 =  torch.cat((pred3, predt1), 2)

        pred1_2 = self.model1_2(pred1,pred2,pred2)

        pred3_2 = self.model3_2(pred3,pred2,pred2)


        pred1=torch.cat((pred1_2, pred3_2), 2)

        
        pred=self.linear(pred1)


        return pred




#Make sequences of shifted timestamps (x0,x1,x2),(x1,x2,x3),(x2,x3,x4)
def shift(data, slices ,step):
	grouped_dataset=[]
	for k in data:
		grouped_data=[]
		for i in range(k.shape[0]-slices+1):
			grouped_data.append(k[i*step:i*step+slices])
		grouped_dataset.append(grouped_data)
	return grouped_dataset



#After splitting the data into sequences of the same video, concat them ignoring the video id
def concat_the_sequences(videos):
	seq=[]
	for video in videos:
		for sequence in video:
			seq.append(sequence)
	return seq


def all_idx(idx, axis):
	grid = np.ogrid[tuple(map(slice, idx.shape))]
	grid.insert(axis, idx)
	return tuple(grid)


def onehot_initialization(a):
	ncols = 4
	out = np.zeros(a.shape + (ncols,), dtype=float)
	out[all_idx(a, axis=2)] =  1
	return out




def train_epoch(model, x_train, y_train, optim1, device):
        model.train()
        epoch_loss, n_correct, n_total= 0,0,0
        inp =  iter(x_train)
        for id_b,batch in enumerate(y_train): 
                optim1.optimizer.zero_grad()
                #Input features
                src = next(inp).to(device)
                
                #src1=src[:,:,:899].clone()
                #src2=src[:,:,900:7043].clone()
                #src3=src[:,:,7044:].clone()
                
                if include_prior==True:
                    prior=src[:,:,-3:]
                    src1=torch.cat((src[:,:,:N1].clone(),prior),2)
                    src2=torch.cat((src[:,:,N1:N1+N2].clone(),prior),2)
                    src3=torch.cat((src[:,:,N1+N2:N1+N2+N3].clone(),prior),2)
                else:
                    src1=src[:,:,:N1].clone()
                    src2=src[:,:,N1:N1+N2].clone()
                    src3=src[:,:,N1+N2:N1+N2+N3].clone()   #ask Mehdi: here src3 is also considering the prior
                    
                #Target starting point
                start_of_sequence = torch.tensor(np.zeros((1,4))).repeat(batch.shape[0],1,1)
                trg =  torch.cat((start_of_sequence, batch), 1)
                #Shift target by one for next token prediction
                target_input = trg[:,:-1,:].to(device).clone()
                target = trg[:,1:,:].to(device)
                _, target = target.max(2) 
                #Make the mask for the next speaker sequences
                src_att1 = torch.ones((src1.shape[0], 1,src1.shape[1])).to(device)
                src_att2 = torch.ones((src2.shape[0], 1,src2.shape[1])).to(device)
                src_att3 = torch.ones((src3.shape[0], 1,src3.shape[1])).to(device)
                
                gth = target_input.size(1)
                trg_att=subsequent_mask(sequence_len).repeat(target.shape[0],1,1).to(device)
                src1=torch.transpose(src1,0,1)
                src2=torch.transpose(src2,0,1)
                src3=torch.transpose(src3,0,1)
                target=torch.transpose(target,0,1)
                target_input=torch.transpose(target_input,0,1)

                pred=model(src1.float(),src2.float(),src3.float(),src_att1,src_att2,src_att3,target_input.float(),trg_att)
                pred=torch.transpose(pred,1,2)
                
                #print(trg_att)
                #print(target_input)
                #print(np.shape(target)) 
                loss1 =criterion1(pred,target)
                loss1.backward()
                optim1.step()
                epoch_loss += loss1.item()
                _, predicted = pred.max(1)
                #_, target = target.max(2)

                #print("predicted=",predicted[0])
                #print("target=",target[0])


                n_correct += predicted.eq(target).sum().item()
                n_total += target.size(0)*target.size(1)
        time_elapsed = datetime.datetime.now() - start_time
        print("Time elapsed:", str(time_elapsed).split(".")[0])
        accuracy=100.*n_correct/n_total
        loss_per_epoch = epoch_loss/len(x_train)
        return loss_per_epoch, accuracy





def eval_epoch(model, x_val, y_val, device):
        model.eval()
        epoch_loss, n_correct, n_total = 0, 0, 0
        inp = iter(x_val)
        inp2 = iter(y_val)
        #batch2=next(inp2).to(device)*0.0
        batch2=torch.tensor(np.zeros((25,10,4))).clone().to(device)
        with torch.no_grad():
            for id_b, batch in enumerate(y_val):
                src = next(inp).to(device)
                
                #src1=src[:,:,:899].clone()
                #src2=src[:,:,900:7043].clone()
                #src3=src[:,:,7044:].clone()
        
                if include_prior==True:
                    prior=src[:,:,-3:]
                    src1=torch.cat((src[:,:,:N1].clone(),prior),2)
                    src2=torch.cat((src[:,:,N1:N1+N2].clone(),prior),2)
                    src3=torch.cat((src[:,:,N1+N2:N1+N2+N3].clone(),prior),2)
                else:
                    src1=src[:,:,:N1].clone()
                    src2=src[:,:,N1:N1+N2].clone()
                    src3=src[:,:,N1+N2:N1+N2+N3].clone()

                #Target starting point
                start_of_sequence = torch.tensor(np.zeros((1,4))).repeat(batch.shape[0],1,1).to(device)
                
                #print(batch2.shape)
                #print(start_of_sequence.shape)
                trg =  torch.cat((start_of_sequence, batch2[:batch.shape[0],:,:]), 1)
                #Shift target by one for next token prediction
                
                target_input = trg[:,:-1,:].to(device)
                target = trg[:,1:,:].to(device)
                _, target = target.max(2) 
                #Make the mask for the next speaker sequences
                src_att1 = torch.ones((src1.shape[0], 1,src1.shape[1])).to(device)
                src_att2 = torch.ones((src2.shape[0], 1,src2.shape[1])).to(device)
                src_att3 = torch.ones((src3.shape[0], 1,src3.shape[1])).to(device)
                sequence_length = target_input.size(1)
                trg_att=subsequent_mask(sequence_length).repeat(target.shape[0],1,1).to(device)
                
                target=torch.transpose(target,0,1)
                target_input=torch.transpose(target_input,0,1)
                src1=torch.transpose(src1,0,1)
                src2=torch.transpose(src2,0,1)
                src3=torch.transpose(src3,0,1)
                
                #print(target_input)
                #print(targ_att)

                pred=model(src1.float(),src2.float(),src3.float(),src_att1,src_att2,src_att3,target_input.float(),trg_att)
               
                #pred = torch.transpose(pred,1,2)
                #del1-Copy1_hardeval.py.swp"

                batch2 = torch.transpose(pred,0,1).clone().to(device)
                #batch2 = pred.clone().to(device)

                pred = torch.transpose(pred,1,2)
                
                _, predicted = pred.max(1)
                loss1 =criterion1(pred,target)
                epoch_loss += loss1.item()
                n_correct += predicted.eq(target).sum().item()
                n_total += target.size(0)*target.size(1) 
        accuracy=100.*n_correct/n_total 
        loss_per_epoch = epoch_loss/len(x_val)
        return loss_per_epoch, accuracy 


#====================================MAIN==========================
# Extract argument flags
args = parser.parse_args()
future_pred = args.future_pred
history_sec = args.history_sec
#modals = args.modals
sequence_len = 10





# if args.include_prior is None:
    # include_prior_list = [True, False]
# elif args.include_prior.lower() == 'true':
    # include_prior_list = [True]
# elif args.include_prior.lower() == 'false':
    # include_prior_list = [False]
# else:
    # raise ValueError('--include prior should be None, "true", or "false')

#val = True
#--------------------------------
modal = 'text_video_voxaudio' 
include_prior_list = [True]
layers = 6
emb_size=512
heads=8
max_epoch=10
warmup = 10
dropout = 0.0
N1=899
N2=6143
N3=1536
heads2=8
bs=25

fun=gaussian

device=torch.device("cuda:1")


log_file='log_run1_prior.txt'


file_to_delete = open(log_file,'w')
file_to_delete.close()


s=f"The parameters are: layer number: {layers}, embedding size: {emb_size}, heads number: {heads}, max epochs: {max_epoch}, warmup: {warmup}, dropout: {dropout} "

with open(log_file, 'a') as the_file:
    the_file.write('\n'+s+'\n\n')


#with open('somefile.txt', 'a') as the_file:
#    the_file.write('Hello\n')

#cpu='store_true'
#device=torch.device("cuda:0")
#cpu='store_true'
#if not torch.cuda.is_available():
#    device=torch.device("cpu")
#verbose=True
#val_size=0
#N = x_val.shape[2]
#---------------------------------


#print(moodel)

#history=[4]
#future=[10]
#future=[10]


history=[4,5,10,30]
future=[1,3,5,10]

history=[30]
future=[1,3,5,10]

dir_path_acc_train = '/home/emincato/job/res_accuracy/LFHTC1/accuracy_train_LFHTC1_P'
dir_path_acc_val = '/home/emincato/job/res_accuracy/LFHTC1/accuracy_val_LFHTC1_P'
dir_path_acc_test = '/home/emincato/job/res_accuracy/LFHTC1/accuracy_test_LFHTC1_P'

whole_res=np.array([])

for include_prior in include_prior_list:
    
    row_res=np.array([])

    for history_sec in history:

        col_res=np.array([])


        for future_pred in future:
                
                flag_settings = {
				'future_pred': future_pred,
				'history_sec': history_sec,
				'modals': modal, #modals
				'include_prior': include_prior, #list
				'sequence_len' : sequence_len}
                
                
                s0='Running with settings: '+ str(flag_settings)
                print(s0)
                
                
                x_train,y_train, x_val, y_val, x_test, y_test = prepare_multiclass_data_from_preprocessed_hdf5(
				modal,
				history_sec,
				future_pred,
				include_prior)            
		
                
                
                #(x_train, x_test, y_train, y_test) = train_test_split(x_train, y_train, test_size=0.40, random_state=42)
				#(x_test, x_val, y_test, y_val) = train_test_split(x_test, y_test, test_size=0.40, random_state=42)
                
                
                x_train = concat_the_sequences(shift(x_train,sequence_len,1))
                y_train = concat_the_sequences(shift(y_train,sequence_len,1))
                x_val = concat_the_sequences(shift(x_val,sequence_len,1))
                y_val = concat_the_sequences(shift(y_val,sequence_len,1))
                x_test = concat_the_sequences(shift(x_test,sequence_len,1))
                y_test = concat_the_sequences(shift(y_test,sequence_len,1))
                
                



                #print(np.shape(np.array(x_train)), np.shape(np.array(y_train)))

                x_train = np.stack(x_train)
                y_train = onehot_initialization(np.stack(y_train))
                x_val = np.stack(x_val)
                y_val = onehot_initialization(np.stack(y_val))
                x_test = np.stack(x_test)
                y_test = onehot_initialization(np.stack(y_test))
            


                x_tr_dl = torch.utils.data.DataLoader(x_train,  batch_size=25)
                y_tr_dl = torch.utils.data.DataLoader(y_train,  batch_size=25)
                x_val_dl = torch.utils.data.DataLoader(x_val, batch_size=25)
                y_val_dl = torch.utils.data.DataLoader(y_val, batch_size=25)
                x_test_dl = torch.utils.data.DataLoader(x_test, batch_size=25)
                y_test_dl = torch.utils.data.DataLoader(y_test, batch_size=25)


            

                #optim =  torch.optim.SGD(model.parameters(), lr=0.01)
                criterion1 = nn.CrossEntropyLoss()
				#criterion2 = nn.CrossEntropyLoss()
				#criterion3 = nn.CrossEntropyLoss()
                
                loss_values, loss_val_values, train_acc_values, val_acc_values, test_acc_values = [] , [] , [] , [], []
				#max_epoch=100
                start_time = datetime.datetime.now()
                


                # ASK Mehdi: Why this if??? 
                if include_prior==True:
                    model1=TransformerEncoder(512, heads, layers).float().to(device)
                    model2=TransformerEncoder(512, heads, layers).float().to(device)
                    model3=TransformerEncoder(512, heads, layers).float().to(device)

                else:

                    model1=TransformerEncoder(512, heads, layers).float().to(device)
                    model2=TransformerEncoder(512, heads, layers).float().to(device)
                    model3=TransformerEncoder(512, heads, layers).float().to(device)


                model4=TransformerEncoder(512, heads, layers).float().to(device)
                model5=TransformerEncoder(512, heads, layers).float().to(device)
                #model5=TransformerEncoder(512, heads, layers, attn_mask=True).float().to(device)
                model6=TransformerEncoder(512, heads, layers).float().to(device)


                model1t = TransformerEncoder(512, heads, layers).float().to(device)
                model2t = TransformerEncoder(512, heads, layers).float().to(device)
                model3t = TransformerEncoder(512, heads, layers).float().to(device)


                model1_2=TransformerEncoder(512, heads2, layers).float().to(device)
                model2_1=TransformerEncoder(512, heads2, layers).float().to(device)
                model1_3=TransformerEncoder(512, heads2, layers).float().to(device)
                model3_1=TransformerEncoder(512, heads2, layers).float().to(device)
                model2_3=TransformerEncoder(512, heads2, layers).float().to(device)
                model3_2=TransformerEncoder(512, heads2, layers).float().to(device)
                model1_1=TransformerEncoder(512, heads2, layers).float().to(device)
                model2_2=TransformerEncoder(512, heads2, layers).float().to(device)
                model3_3=TransformerEncoder(512, heads2, layers).float().to(device)



                att_layer=TransformerEncoder(1024, heads2, layers).float().to(device)
                att_layer2=TransformerEncoder(1024, heads2, layers).float().to(device)


                model=MyEnsemble(model1,model2,model3,model4, model5, model6, model1t,model2t,model3t,model1_2,model2_1,model1_3,model3_1,model2_3,model3_2,model1_1,model2_2,model3_3,att_layer,att_layer2)
                



                optim1 = NoamOpt(512, 1., len(x_tr_dl)*warmup,torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.98), eps=1e-9, weight_decay=1e-7))
                

                best_val_acc = 0.0
                best_test_acc= 0.0
                #start_time = datetime.datetime.now()
                
                
                with open(log_file, 'a') as the_file:
                    the_file.write('\n'+s0+'\n\n')
                
                
                for epoch in range(max_epoch): 
                    train_loss, train_accuracy = train_epoch(model, x_tr_dl, y_tr_dl,optim1,device)
                    loss_values.append(train_loss)
                    train_acc_values.append(train_accuracy)
                    s1=f'Epoch: {(epoch)+1:03d}/{(max_epoch):03d} | Train Loss: {(train_loss):.3f} | Accuracy: {(train_accuracy):.3f}'
                    print(s1)
                    #print(f'Epoch: {(epoch)+1:03d}/{(max_epoch):03d} | Train Loss: {(train_loss):.3f} | Accuracy: {(train_accuracy):.3f}')
                    val_loss, val_accuracy = eval_epoch(model, x_val_dl, y_val_dl, device)
                    loss_val_values.append(val_loss)
                    val_acc_values.append(val_accuracy)
                    s2=f'Epoch: {(epoch)+1:03d}/{(max_epoch):03d} | Val Loss: {(val_loss):.3f} | Accuracy: {(val_accuracy):.3f}'
                    print(s2)
                    test_loss,test_accuracy = eval_epoch(model, x_test_dl, y_test_dl, device)
                    test_acc_values.append(test_accuracy)
                    s3=f'Epoch: {(epoch)+1:03d}/{(max_epoch):03d} | Test Loss: {(test_loss):.3f} | Accuracy: {(test_accuracy):.3f}'
                    print(s3)
                    #print("The best test accuracy so far is: ",test_accuracy)


                    if val_accuracy>best_val_acc:
                        best_val_acc = val_accuracy
                        best_test_acc = test_accuracy
                        #torch.save(model, 'best_model1')
                        print("The best test accuracy so far is: ",best_test_acc)
                        s4=f'The best test accuracy so far is: {best_test_acc}'
                    else:
                        print("The best test accuracy so far is: ",best_test_acc)
                        s4=f'The best test accuracy so far is: {best_test_acc}'

                    


                    with open(log_file, 'a') as the_file:
                        the_file.write(s1+'\n')
                        the_file.write(s2+'\n')
                        the_file.write(s3+'\n')
                        the_file.write(s4+'\n\n')



                #np.save(dir_path_acc_train + str(history_sec)+"_F_"+str(future_pred)+"_pr_T.npy", train_acc_values)
                #np.save(dir_path_acc_val + str(history_sec)+"_F_"+str(future_pred)+"_pr_T.npy", val_acc_values)
                #np.save(dir_path_acc_test + str(history_sec)+"_F_"+str(future_pred)+"_pr_T.npy", test_acc_values)

                col_res=np.append(col_res,best_test_acc)
                
                print(col_res)
                
                # deleting al the model and the numpy array to free the memory space
                del model
                del model1
                del model2
                del model3
                del model4
                del model5
                del model6
                del model1t
                del model2t
                del model3t
                del model1_2
                del model1_3
                del model2_1
                del model3_1
                del model2_3
                del model3_2
                del model1_1
                del model2_2
                del model3_3
                del x_train
                del y_train
                del x_val 
                del y_val
                del x_test 
                del y_test
                
                gc.collect()

                
                
        row_res=np.append(row_res,col_res)

        with open(log_file, 'a') as the_file:
            the_file.write(str(row_res))


    whole_res=np.append(whole_res,row_res)
        
        
    

print(whole_res)

with open(log_file, 'a') as the_file:
    the_file.write("\n")
    the_file.write(str(whole_res))





