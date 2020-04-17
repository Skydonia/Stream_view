# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 17:54:34 2020

@author: Lebas Bastien
"""

from pyvis.network import Network
import requests
import numpy as np
import time
import copy

#%%ID
client_id='yoltz3q3n3eyehtnsuqyqhw7auqbcw'
Header={'Client-ID':client_id}
twitch_api_params = {
    'client_id': client_id,   # Required
    'api_version': 5,         # Required
    'game': '',               # Optional
    'limit': 100,               # Optional, defaults to 25. Max is 100.
    'language': 'fr'
    }
#%%Couleurs
def import_color():
    List_couleur=[]
    with open('code.txt','r') as f1:
        for i,line in enumerate(f1):
            code=line.split("\n")[0]
            List_couleur.append(code)
    return List_couleur

def chose_color(List_couleur):
    indice=np.random.randint(120)
    return List_couleur[indice]

List_couleur=import_color()

#%%Classes

class Tree:
    def __init__(self, name):
        self.name=name
        self.date=time.time()
        self.streamers = []
        self.groupes_migrants={}
        
    def update_streamers(self,channel_list):
        self.streamers=[]
        for name in channel_list['streams']:
            self.streamers.append(Streamer(name['channel']['name']))
        return
    
    def update_chats(self):
        for streamer in self.streamers:
            streamer.update_chat()
        return
    
    def ini_groupes_migrants(self):
        groupe={}
        for streamer_depart in self.streamers:
            for streamer_arrivee in self.streamers:
                if streamer_depart!=streamer_arrivee:
                    groupe[streamer_depart.name,streamer_arrivee.name]=[]
        self.groupes_migrants=groupe
        return
        
    def update_groupes_migrants(self):
        for streamer_depart in self.streamers:
            for viewer in streamer_depart.viewer_out:
                for streamer_arrivee in self.streamers:
                    if viewer in streamer_arrivee.viewer_in:
                        try:
                            self.groupes_migrants[streamer_depart.name,streamer_arrivee.name].append(viewer)
                            streamer_depart.viewer_out.remove(viewer)
                            streamer_arrivee.viewer_in.remove(viewer)
                        except KeyError:
                            self.groupes_migrants[streamer_depart.name,streamer_arrivee.name]=[viewer]
                            streamer_depart.viewer_out.remove(viewer)
                            streamer_arrivee.viewer_in.remove(viewer)
                        break
        return
                            
    

class Streamer:
    def __init__(self, name):
        self.name=name
        try:
            self.photo_profil=requests.get('https://api.twitch.tv/helix/users?login='+self.name,headers=Header).json()['data'][0]['profile_image_url']
        except KeyError:#en cas de bug de chargement d'image
            self.photo_profil='./images/default.jpg'
        self.chat=requests.get('https://tmi.twitch.tv/group/user/'+self.name+'/chatters').json()['chatters']['viewers']
        self.ancien_chat=[]#juste pour initialiser
        self.poids=len(self.chat)
        self.viewer_out=[]
        self.viewer_in=[]
        self.couleur=chose_color(List_couleur)
        

    def update_chat(self):
        self.ancien_chat=copy.deepcopy(self.chat)
        while self.chat==self.ancien_chat:
            self.chat=requests.get('https://tmi.twitch.tv/group/user/'+self.name+'/chatters').json()['chatters']['viewers']
        self.poids=len(self.chat)
        self.viewers_en_migration()
        return
        
    def viewers_en_migration(self):
        if self.ancien_chat==self.chat:
            print('gros con de merde')
        for viewer in self.ancien_chat:
            if viewer not in self.chat:
                self.viewer_out.append(viewer)
        for viewer in self.chat:
            if viewer not in self.ancien_chat:
                self.viewer_in.append(viewer)
        return          

#%%
def generate_graph(arbre):
    got_net = Network(height="100%", width="100%", bgcolor="#222222", font_color="white")
    dico_couleur={}
    for streamer in arbre.streamers:   
        got_net.add_node(streamer.name, value=streamer.poids,shape='image',image=streamer.photo_profil,size=100)
        dico_couleur[streamer.name]=streamer.couleur
    
    for depart,arrivee in arbre.groupes_migrants:
        for viewer in arbre.groupes_migrants[depart,arrivee]:
            got_net.add_node(viewer,value=1,color=dico_couleur[depart])
            got_net.add_edge(viewer,depart,color=dico_couleur[depart])
            got_net.add_edge(viewer,arrivee,color=dico_couleur[arrivee])
    got_net.show_buttons()
    got_net.set_edge_smooth(smooth_type='dynamic')
    got_net.force_atlas_2based(gravity=-200,central_gravity=0.01,spring_length=1,spring_strength=0.08,damping=0.4,overlap=0)
    got_net.save_graph("./graphs_v1/" + 'streamgame_v1_42' + ".html")
    return


#%%Calculs

stream_game=Tree('stream_game')
channel_list = requests.get('https://api.twitch.tv/kraken/streams/',params=twitch_api_params).json()
stream_game.update_streamers(channel_list)
#time.sleep(300)
stream_game.update_chats()
stream_game.ini_groupes_migrants()
stream_game.update_groupes_migrants()
generate_graph(stream_game)