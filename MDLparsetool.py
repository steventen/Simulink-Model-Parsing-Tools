#!/usr/bin/env python
from pyparsing import *
import re
import string

"""
This tool is for manipulating Simulink model file under Python

Methods:
get_param(mdlSys, attriName[, ex = 1])
set_param(mdlSys, attriName, attriValue)
find_block(mdlSys, obj, attriName, keyVal)
get_connection(mdlSys, jointList)

Take a look at main() part to learn how to use them

Author: Steven Yue
E-mail: steventenie@gmail.com

Credits:
Code for parsing mdl file into nest list was writtern by Kjell Magne Fauske,
and most of his code is based on the json parser example distributed with
pyparsing. The code in jsonParser.py was written by Paul McGuire

"""

# A high level grammar of the Simulink mdl file format
SIMULINK_BNF = """
object {
     members
}
members
    variablename  value
    object {
        members
    }
variablename

array
    [ elements ]
matrix
    [elements ; elements]
elements
    value
    elements , value
value
    string
    doublequotedstring
    float
    integer
    object
    array
    matrix
"""


# parse actions
def convertNumbers(s,l,toks):
    """Convert tokens to int or float"""
    # Taken from jsonParser.py
    n = toks[0]
    try:
        return int(n)
    except ValueError as ve:
        return float(n)

def joinStrings(s,l,toks):
    """Join string split over multiple lines"""
    return ["".join(toks)]


def mdlParser(mdlFilePath):
	mdldata = open(mdlFilePath,'r').read()
	# Define grammar

	# Parse double quoted strings. Ideally we should have used the simple statement:
	#    dblString = dblQuotedString.setParseAction( removeQuotes )
	# Unfortunately dblQuotedString does not handle special chars like \n \t,
	# so we have to use a custom regex instead.
	# See http://pyparsing.wikispaces.com/message/view/home/3778969 for details. 
	dblString = Regex(r'\"(?:\\\"|\\\\|[^"])*\"', re.MULTILINE)
	dblString.setParseAction( removeQuotes )
	mdlNumber = Combine( Optional('-') + ( '0' | Word('123456789',nums) ) +
						Optional( '.' + Word(nums) ) +
						Optional( Word('eE',exact=1) + Word(nums+'+-',nums) ) )
	mdlObject = Forward()
	mdlName = Word('$'+'.'+'_'+alphas+nums)
	mdlValue = Forward()
	# Strings can be split over multiple lines
	mdlString = dblString + ZeroOrMore(Suppress(LineEnd()) + dblString)
	mdlString.set_parse_action(lambda lst: "".join(lst))
	mdlElements = delimitedList( mdlValue )
	mdlArray = Group(Suppress('[') + Optional(mdlElements) + Suppress(']') )
	mdlMatrix =Group(Suppress('[') + (delimitedList(Group(mdlElements),';')) \
				  + Suppress(']') )
	mdlValue << ( mdlNumber | mdlName| mdlString  | mdlArray | mdlMatrix )
	memberDef = Group( mdlName  + mdlValue ) | Group(mdlObject)
	mdlMembers = OneOrMore( memberDef)
	mdlObject << ( mdlName+Suppress('{') + Optional(mdlMembers) + Suppress('}') )
	mdlNumber.setParseAction( convertNumbers )
	mdlString.setParseAction(joinStrings)
	# Some mdl files from Mathworks start with a comment. Ignore all
	# lines that start with a #
	singleLineComment = Group("#" + restOfLine)
	mdlObject.ignore(singleLineComment)
	mdlparser = mdlObject
	result = mdlparser.parseString(mdldata)
	return result

def get_param(mdlSys, attriName, ex = 1):
	""" 
	Find the value of a special attribute in the mdl system sequence
		If ex = 1 : list [Block Name, value]
		If ex = 0 : list only the value of the attribute
	"""
	result = []
	for syslist in mdlSys:
		if syslist[0]=='System':
			for blocklist in syslist:
				if blocklist[0]=='Block':
					for item in blocklist:
						if item[0]== attriName:
							if ex == 1:
								ans = [blocklist[2][1], item[1]]
							elif ex == 0:
								ans = item[1]
							result.append(ans)
	
	if result == []:
		for blocklist in mdlSys:
			if blocklist[0]=='Block':
				for item in blocklist:
					if item[0]== attriName:
						if ex == 1:
							ans = [blocklist[2][1], item[1]]
						elif ex == 0:
							ans = item[1]
						result.append(ans)
	if result == []:
		for blocklist in mdlSys:
			for item in blocklist:
				if item[0]== attriName:
					if ex == 1:
						ans = [blocklist[2][1], item[1]]
					elif ex == 0:
						ans = item[1]
					result.append(ans)
	if result == []:
		for item in mdlSys:
			if item[0]== attriName:
				if ex == 1:
					ans = [blocklist[2][1], item[1]]
				elif ex == 0:
					ans = item[1]
				result.append(ans)
	return result


def set_param(mdlSys, attriName, attriValue):
	""" 
	Set the value of a special attribute in the mdl system sequence
		If ex = 1 : list [Block Name, value]
		If ex = 0 : list only the value of the attribute
	Return  1 if find and set the parameter successfully
		0 if failed	
	"""
	result = 0
	for syslist in mdlSys:
		if syslist[0]=='System':
			for blocklist in syslist:
				if blocklist[0]=='Block':
					for item in blocklist:
						if item[0]== attriName:
							item[1] = attriValue
							result = 1	
	if result == 0:
		for blocklist in mdlSys:
			if blocklist[0]=='Block':
				for item in blocklist:
					if item[0]== attriName:
						item[1] = attriValue
						result = 1
	if result == 0:
		for blocklist in mdlSys:
			for item in blocklist:
				if item[0]== attriName:
					item[1] = attriValue
					result = 1
	if result == 0:
		for item in mdlSys:
			if item[0]== attriName:
				item[1] = attriValue
				result = 1
	return result


def find_block(mdlSys, obj, attriName, keyVal):
	"""
	Find all the Blocks that has an keyVal in an Attribute
	"""
	result = []
	for syslist in mdlSys:
		if syslist[0]=='System':
			for blocklist in syslist:
				if blocklist[0]== obj:
					for item in blocklist:
						if item[0]== attriName and item[1]==keyVal:
							ans = blocklist
							
							result.append(ans)
	return result
	
	
def get_connection(mdlSys, jointList):
	lineList = find_block(mdlSys,'Line','LineType','Connection')
	jointConnList = []
	for jointName in jointList:
		jointConn = [jointName]
		jointBlockList = find_block(mdlSys,'Block', 'Name', jointName)
		jointFramesList = get_param(jointBlockList, 'PrimitiveProps', ex = 0)
		jointFrames = jointFramesList[0].split('$')
		joint_Axis = jointFrames[2]
		joint_TypeName=get_param(jointBlockList,'SourceType',0)[0]
		jointConn.append(joint_TypeName)
		jointConn.append(joint_Axis)
		joint_relCS = jointFrames[1]
		jointConn.append(joint_relCS)
		
		for blocklist in lineList:
			for item in blocklist:
				if item[0] == 'DstBlock' and item[1] == jointName:
					baseName = get_param(blocklist, 'SrcBlock', ex = 0)
					basePortList = get_param(blocklist, 'SrcPort', ex = 0)
					basePortVal = basePortList[0]
					basePort = basePortVal.split('Conn')
					baseBlock = find_block(mdlSys,'Block', 'Name', baseName[0])
					
					bconnCSValList = get_param(baseBlock, basePort[0]+'ConnTagsString', ex = 0)
					if bconnCSValList == []:
						bconnCSValList = ['None']
					
					bconnCSVal = bconnCSValList[0]
					numCS = eval(basePort[-1])
					baseConn = bconnCSVal.split('|')[numCS - 1]  #Find the digital number of CS which is the base to connect to the joint
					
					jointConn.append([baseName[0], baseConn])
				
				if item[0] == 'SrcBlock' and item[1] == jointName:
					followerName = get_param(blocklist, 'DstBlock', ex = 0)
					
					followerPortList = get_param(blocklist, 'DstPort', ex = 0)  #Note: get_param() returns a list
					followerPortVal = followerPortList[0]
					followerPort = followerPortVal.split('Conn')
					followerBlock = find_block(mdlSys,'Block', 'Name', followerName[0])
					
					fconnCSValList = get_param(followerBlock, followerPort[0]+'ConnTagsString', ex = 0)
					if fconnCSValList == []:
						fconnCSValList = ['None']
						
					fconnCSVal = fconnCSValList[0]
					numCS = eval(followerPort[-1])
					followerConn = fconnCSVal.split('|')[numCS - 1]  #Find the digital number of CS which is the base to connect to the joint
					jointConn.append([followerName[0], followerConn])
				
		jointConnList.append(jointConn)						

	return jointConnList

# examples on how to use thoes functions
def main():
	import os
	from pprint import pprint
	filePath = os.path.join(os.getcwd(),'testExample','fourBar.mdl')
	#testdata = open('AIRCRAFT_ENGINE.mdl','r').read()
	result = mdlParser(filePath)
	mdldata = result.asList()
	#mdldata = result
	
	JointList = find_block(mdldata,'Block','DialogClass','JointBlock')
	JointNameList = get_param(JointList,'Name',0)
	ConnList = get_connection(mdldata, JointNameList)
	print('ConnList')
	pprint(ConnList)
	print('ConnList[1]')
	pprint(ConnList[1])
	print('ConnList[1][1]')
	pprint(ConnList[1][1])
	fListT = open('fourBarTemplete.txt','wb')


# test stuff
if __name__ == '__main__':
	main()

			

#for index, item in enumerate(seq):
#		print 1
#		if value in item:
#			return index, item
