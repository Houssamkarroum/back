from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
import os


load_dotenv()


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Initialize components
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = FAISS.load_local(
    "faiss_medical_index",
    embeddings,
    allow_dangerous_deserialization=True
)


llm = ChatOpenAI(
    model_name="gpt-4-turbo",
    temperature=0.3,
    max_tokens=1000
)


qa = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vector_store.as_retriever()
)


# Domain specialization prompt
DOMAIN_SPECIALIZATION_PROMPT = """
You are a medical assistant specialized in providing information about {domain}.
Your knowledge is limited to this domain.


When asked a question:
1. First determine if the question is related to {domain}
2. If it is related, answer using the provided context
3. If not, respond with: "هذا خارج نطاق تخصصي في"


Current domain: {domain}
"""


DOMAIN = "الغدد الصماء"  # Example domain specialization


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_query = data.get('query', '')
       
        if not user_query:
            return jsonify({"error": "Query is required"}), 400
       
        # Translate AR → EN
        translated_query = GoogleTranslator(source='ar', target='en').translate(user_query)


        full_prompt = DOMAIN_SPECIALIZATION_PROMPT.format(domain=DOMAIN)


        # Get response
        # Get response with domain specialization
        response = qa.run({
            "query": translated_query,
            "prompt": full_prompt
        })        
        # Translate EN → AR
        translated_response = GoogleTranslator(source='en', target='ar').translate(response)
       
        return jsonify({
            "query": user_query,
            "response": translated_response
        })
   
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)


