from openai import OpenAI
import os

client = OpenAI(
api_key=os.environ["GEMINI_API_KEY"],
base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

tools = [
  {
     "type": "function",
         "function" : {
             "name" : "get_flight_info",

           "description" : "Get information about a flight.",
           "parameters" : {
               "type" : "object",
               "properties" : {


                 "flight_number": {
                      "type": "string",
                      "description": "Flight number"
                  }
           },
           "required": ["flight_number"]
       }
    }
  }
]

response = client.chat.completions.create(
   model="gemini-3.6-flash",
   messages=[
      {
         "role" : "user",
         "content": "Check the status of flight CA1234."
      }
   ],
   tools=tools,
   tool_choice="auto"
)

print(response)
