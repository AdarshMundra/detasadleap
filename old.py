import json
import requests
import boto3
from decimal import Decimal
import urllib3
http = urllib3.PoolManager()
from boto3.dynamodb.conditions import Key
dynamodb = boto3.resource('dynamodb')
Question_Data = dynamodb.Table('Question_Prod')
Token_Data = dynamodb.Table('Token_Prod')
Record = dynamodb.Table("Record_Prod")
from difflib import SequenceMatcher
def ResponseData(options,answer):
    answer="".join(answer.split()).lower()
    for j in range(0,len(options)):
        i=options[j].split(" ")[1:]
        i="".join(i).lower()
        z=SequenceMatcher(a=answer,b=i).ratio()
        if z > .92:
            break
    if j==4:
        if z > .92:
            return j,True
        else:
            return False,False
    else:
        return j,True


def check_key(key, dictionary_list):
    for dictionary in dictionary_list:
        if key in dictionary:
            return True
    return False

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError

def lambda_handler(event, context):
    print(event)
    avatar=event['fm-avatar']
    avatar=json.loads(avatar)
    Custom = event['fm-custom-data']
    Custom=json.loads(Custom)
    token1 = event['sid']
    email = Custom['email']

    if avatar['type']=="WELCOME":
        data1="Hi "+ Custom['name']+"! Welcome to the world of e-dee-YOU! I'm Hannah! How can I help you?"
    else:

        if len(event['fm-question'])==0:
            # data1 = "Can you please repeat?"
            # data1 = "Please enter your query."
            # data1 = "Please try again."
            data1 = "I didn't hear anything, please try again." 
        elif event['fm-question'].lower() =='fine':
            data1 ="Great."     
 
        elif event['fm-question'].lower() =='stop':
            data1 ="Closing the quiz." 
        
        elif event['fm-question'].lower() =='i am here':
            data1 ="Ok, Good." 
    
        elif event['fm-question'].lower() =='no':
            data1 = "Ok. Take a break.<br>You can say 'Stop' to close the test."    
        
        elif event['fm-question'].lower() =='repeat':
            Token_Data_Response = Token_Data.get_item(Key={'token' : token1})
            if 'QuestionId' in Token_Data_Response['Item']:
                QID = Token_Data_Response['Item']['QuestionId']
                Record_Response = Record.get_item(Key={'userId' :email,'QuestionId':QID})
                Record_Response = Record_Response['Item']
                Qdata = Record_Response['Question'][int(Record_Response['CurrentPostion'])]
                options = Qdata["options"]
                Question = Qdata["Question"]
                AC = Question + "<br>\n"
                html = "<ul>\n"
                for option in options:
                    html += f"{option}<br>\n"
                html += "</ul>"
                
                data1 =AC + html

            else:
                data1 = "Can you please repeat the sentance."
        elif event['fm-question'].lower() =='yes':
            Token_Data_Response = Token_Data.get_item(Key={'token' : token1})
            if 'QuestionId' in Token_Data_Response['Item']:
                QID = Token_Data_Response['Item']['QuestionId']
                Record_Response = Record.get_item(Key={'userId' :email,'QuestionId':QID})
                Record_Response = Record_Response['Item']
                CurrentPostion=Record_Response['CurrentPostion']
                if CurrentPostion <=Record_Response['Total Question'] -1:
                    CurrentPostion1=int(CurrentPostion)+1
                    Qdata = Record_Response['Question'][int(CurrentPostion)]
                    options = Qdata["options"]
                    Question = Qdata["Question"]
                    AC ="Question "+str(CurrentPostion1)+". "+ Question + "<br>\n"
                    html = "<ul>\n"
                    for option in options:
                        html += f"{option}<br>\n"
                    html += "</ul>"
                    data1 =AC + html
                    # Record_Response['CurrentPostion'] = CurrentPostion+1
                    # Record_Response['CurrentAnswerPostion']=Record_Response['CurrentAnswerPostion']+1
                    # Record_Response=json.dumps(Record_Response, default=decimal_default)
                    # Record.put_item(Item = Record_Response)
                
            
                else:
                    Record_Response['CurrentPostion'] = 0
                    Record_Response['CurrentAnswerPostion']=0
                    Record_Response['TestSeriesStatus'] = 0
                    Qdata = Question_Data.get_item(Key={'id':QID})
                    Record_Response["Total Question"]=len(Qdata['Item']['question'])
                    Record_Response['Question']=Qdata['Item']['question']
                    Record.put_item(Item = Record_Response)
                
                    data1="The test is completed. Please say or write 'Stop' to exit."
            else:
                data1 = "Can you please repeat the sentance."
        else:
            Token_Data_Response = Token_Data.get_item(Key={'token' : token1})
            if 'QuestionId' in Token_Data_Response['Item']:
                QID = Token_Data_Response['Item']['QuestionId']
                Record_Response = Record.get_item(Key={'userId' :email,'QuestionId':QID})
                Record_Response = Record_Response['Item']
                # print(Record_Response['CurrentPostion'])
            else:
                Record_Response={}
            if "Question" in Record_Response:
                if int(Record_Response['Total Question']) == int(Record_Response['CurrentPostion']):
                    Value = False
                else:
                    answerdata,Value= ResponseData(Record_Response['Question'][int(Record_Response['CurrentPostion'])]['options'],event["fm-question"])
            else:
                Value=False
            l=[]
            if Value ==False:
                url ="http://52.11.66.129:5002/webhooks/rest/webhook"
                # url="http://54.184.113.39:5002/webhooks/rest/webhook" 
                encoded_data = json.dumps({  "sender": "adarsh","message": event["fm-question"]})
                resp = http.request('POST',url,body=encoded_data,headers={'Content-Type': 'application/json'})
                data=json.loads(resp.data.decode('utf-8'))
                # print(data)
                if len(data)==0:
                    
                    data1 ="Sorry, I don't understand. Can you please repeat?"
                for i in range(0,len(data)):
                    data1=data[i]['text']
                    
                    if data1 in ['0','1','2','3','4']:           
                        description=Record_Response['Question'][int(Record_Response['CurrentPostion'])]['description']
                        data1=int(data1)
                        correctPostioin =int(Record_Response['Question'][int(Record_Response['CurrentPostion'])]['correctPostioin'])
                        if data1 == correctPostioin:
                            Record_Response['CorrectAnswerbyYou']=Record_Response['CorrectAnswerbyYou']+1
                            Record_Response['TestSeriesStatus'] ="Resume"
                            Record_Response['CurrentAnswerPostion']=Record_Response['CurrentAnswerPostion']+1
                            Record_Response['CurrentPostion']=Record_Response['CurrentPostion']+1
                            l.append(description[data1])
                            l.append("<br><br>Shall we move to the next question?")
                            data1 = ' '.join(l)
                            Record.put_item(Item = Record_Response)
                            # print(data1)
                        else:
                            data1=description[data1]
                            l.append(data1)
                            l.append("<br>The correct Answer is - ")
                            correctAnswer = Record_Response['Question'][int(Record_Response['CurrentPostion'])]['correctAnswer']
                            correctAnswer = correctAnswer[3:] 
                            correctAnswer = correctAnswer.split('.')[0]
                            l.append('"'+correctAnswer+'".')
                            Record_Response['TestSeriesStatus'] ="Resume"
                            Record_Response['CurrentAnswerPostion']=Record_Response['CurrentAnswerPostion']+1
                            Record_Response['CurrentPostion']=Record_Response['CurrentPostion']+1
                            Record.put_item(Item = Record_Response)

                            l.append("<br><br>Shall we move to the next question?")
                            data1 = ' '.join(l)
                            # print(data1)
                    else:
                        if data1 =='repeat':
                            data1 =get_question_html(Record_Response)
                        elif data1 =='yes':
                            data1  = get_next_question_html(token1,email) 
                            # print(data1)
                        elif data1 =='stop':
                            data1 ="Closing the quiz." 
                        else:
                            l.append(data1)
                            # l.append('<br>')
                            data1 = ' '.join(l)            
                
                # data1 = "Can you please repeat"
            else:
                correctPostioin =int(Record_Response['Question'][int(Record_Response['CurrentPostion'])]['correctPostioin'])
                description = Record_Response['Question'][int(Record_Response['CurrentPostion'])]['description']

                if answerdata == correctPostioin:
                    Record_Response['CorrectAnswerbyYou']=Record_Response['CorrectAnswerbyYou']+1
                    Record_Response['CurrentAnswerPostion'] =Record_Response['CurrentAnswerPostion']+1
                    Record_Response['CurrentPostion']=Record_Response['CurrentPostion']+1
                    Record_Response['TestSeriesStatus'] ="Resume"
                    l.append(description[answerdata])
                    l.append("<br><br>Shall we move to the next question?")
                    data1 = ' '.join(l)
                    Record.put_item(Item = Record_Response)

                else:
                    data1=description[answerdata]
                    l.append(data1)
                    l.append("<br>The correct Answer is - ")
                    correctAnswer = Record_Response['Question'][int(Record_Response['CurrentPostion'])]['correctAnswer']
                    correctAnswer = correctAnswer[3:]
                    correctAnswer = correctAnswer.split('.')[0]
                    l.append('"'+correctAnswer+'".')
                    Record_Response['TestSeriesStatus'] ="Resume"
                    Record_Response['CurrentAnswerPostion'] =Record_Response['CurrentAnswerPostion']+1
                    Record_Response['CurrentPostion']=Record_Response['CurrentPostion']+1
                    Record.put_item(Item = Record_Response)
                    l.append("<br><br>Shall we move to the next question?")
                    data1 = ' '.join(l)





    
    dici={'answer':data1}    
    return{
        'answer':json.dumps(dici),
        "matchedContext": "",
        "conversationPayload": "{}"
    }













    
def is_json(my_json):
  try:
    json_object = json.loads(my_json)
  except ValueError:
    return False
  return True

def get_question_html(Record_Response):
    Qdata = Record_Response['Question'][int(Record_Response['CurrentPostion'])]
    options = Qdata["options"]
    Question = Qdata["Question"]
    AC = Question + "<br>\n"
    html = "<ul>\n"
    for option in options:
        html += f"{option}<br>\n"
    html += "</ul>"
    
    return AC + html
    


def get_next_question_html(token1, email):
    Token_Data_Response = Token_Data.get_item(Key={'token': token1})
    if 'QuestionId' in Token_Data_Response['Item']:
        QID = Token_Data_Response['Item']['QuestionId']
        Record_Response = Record.get_item(Key={'userId': email, 'QuestionId': QID})
        Record_Response = Record_Response['Item']
        CurrentPostion = Record_Response['CurrentPostion']
        if CurrentPostion <= Record_Response['Total Question']-1:
            CurrentPostion1 = int(CurrentPostion)+1
            Qdata = Record_Response['Question'][int(Record_Response['CurrentPostion'])]
            options = Qdata["options"]
            Question = Qdata["Question"]
            AC ="Question "+str(CurrentPostion1)+". "+ Question + "<br>\n"
            html = "<ul>\n"
            for option in options:
                html += f"{option}<br>\n"
            html += "</ul>"
            data1 = AC + html
            # Record_Response['CurrentPostion'] = CurrentPostion+1
            # Record_Response['CurrentAnswerPostion']=Record_Response['CurrentAnswerPostion']+1
            # Record.put_item(Item=Record_Response)
            return data1
        else:
            Record_Response['CurrentPostion'] = 0
            Record_Response['CurrentAnswerPostion']= 0
            Record_Response['TestSeriesStatus'] = 0
            Record.put_item(Item=Record_Response)
            return "The test is complete. Please say or write 'Stop' to exit."
    else:
        return "Please start the test first."
