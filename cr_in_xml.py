#!/usr/bin/env python
#encoding=UTF-8
#  
#  Copyright 2014 MopperWhite <mopperwhite@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
from xml.etree import ElementTree as ET
import os,re,random,time,json
import BeautifulSoup as BS
class ReplyException(Exception):pass
class ReplyDB(object):
        def __init__(self,db_file):
                self.db_file=db_file
                if os.path.exists(db_file):
                        self.db_tree=ET.parse(db_file)
                        self.db_root=self.db_tree.getroot()
                        self.h_root=self.db_root.find("./history")
                        self.r_root=self.db_root.find("./reply")
                else:
                        self.db_root=ET.Element("cr")
                        self.db_tree=ET.ElementTree(self.db_root)
                        self.h_root=ET.SubElement(self.db_root,"history")
                        self.r_root=ET.SubElement(self.db_root,"reply")
                        self.write()
        def get_reply(self,input_):
                def score_key(key_element):
                        r=re.search(key_element.text,input_,flags=re.I)
                        if r:return (key_element,len(r.group(0)))
                        else:return (key_element,0)
                kl=self.db_root.findall("./reply/group/key")
                if not kl:raise ReplyException(u"数据库是空的！")
                best_key,score=max(map(score_key,kl),key=lambda x:x[1])
                if score==0:
                        raise ReplyException(u"不知道该怎么回答.")
                else:
                        vl=self.db_root.findall("./reply/group[@id='%s']/value"%best_key.get("group"))
                        if not vl:raise ReplyException(u"我知道这个但是不知道怎么说……")
                        return random.choice(vl).text
                        
        def has_key(self,key):
                return self._has(key,"key")
        def has_value(self,value):
                return self._has(value,"value")
        def _has(self,value,type_):
                return self.db_root.find("./reply/group[%s='%s']"%(type_,value)) is not None
        def add_key_by_key(self,new_key,key):
                self._add_by_key(new_key,key,"key")
        def add_value_by_key(self,new_value,key):
                self._add_by_key(new_value,key,"value")
        def _add_by_key(self,value,key,type_):
                group=self.db_root.find("./reply/group[key='%s']"%key)
                if group is not None:
                        return self._add_by_group(value,group.get("id"),type_)
                else:
                        raise ReplyException(u"不存在的关键字:  "+key)
        def add_key_by_group(self,new_key,group_id):
                return self._add_by_group(new_key,group_id,"key")
        def add_value_by_group(self,new_value,group_id):
                return self._add_by_group(new_value,group_id,"value")
        def _add_by_group(self,value,group_id,type_):
                group=self.get_group_by_id(group_id)
                element=ET.SubElement(group,type_)
                element.set("group",group_id)
                element.text=value
                return element               
                
        def get_group_by_id(self,id_):
                return self.db_root.find("./reply/group[@id='%s']"%id_)
        def add_group(self,keys=[],values=[]):
                id_=str(len(self.db_root.findall("./reply/group")))
                parent=self.db_root.find("./reply")
                group=ET.SubElement(parent,"group")
                group.set("id",id_)
                for k in keys:
                        self.add_key_by_group(k,id_)
                for v in values:
                        self.add_value_by_group(v,id_)        
                return group
        
        def add_history(self,username,reply_index,text=""):
                entry=ET.SubElement(self.h_root,"entry")
                entry.set("username",username)
                entry.set("reply_index",str(reply_index))
                entry.text=text
                self.write()
                return entry
        def input_line(self,line):
                r=re.search(r"^\/(\w*)(.*)",line)
                if r:
                        command,arg_string=r.groups()
                        if not arg_string or arg_string.isspace():
                                args=()
                        else:
                                args=arg_string.split()
                        return self.run_command(command,args)
                else:
                        return self.get_reply(line)
        def run_command(self,command,args):
                func=vars(self.__class__).get("do_"+command)
                if func:
                        try:
                                return func(self,*args)
                        except TypeError:
                                raise ReplyException(u"参数错误.")
                else:
                        raise ReplyException( u"未知命令.")
        def write(self):
                self.db_tree.write(open(self.db_file,'w'))
        def clear_history(self):
                self.h_root.clear()
                self.write()
        def do_teach(self,key,*values):
                if not values:raise TypeError()
                if self.has_key(key):
                        for v in values:
                                self.add_value_by_key(v,key)
                else:
                        self.add_group([key],values)
                self.write()
                return u"调教成功."
        def do_alias(self,key,*aliases):
                if not aliases:raise TypeError()
                if self.has_key(key):
                        for v in aliases:
                                self.add_key_by_key(v,key)
                else:
                        self.add_group((key,)+aliases)
                self.write()
                return u"调教成功."
def cli():
        print "ChattingRobot"
        print "/teach [key] [reply] [reply] ..."
        print "/alias [key] [alias] [alias] ..."
        db=ReplyDB("test_dbs.xml")
        import locale
        while 1:
                try:
                        s=raw_input(":").decode(locale.getdefaultlocale()[1])
                except EOFError as e:
                        exit(0)
                if s:
                        try:
                                print db.input_line(s)
                        except ReplyException as e:
                                print "Error:",e.message
if __name__=='__main__':
        cli()
