from flask import Flask
from utils import Service, encode_image
import base64
from flask import make_response, request, current_app
from flask import *
from flask import send_from_directory
import requests as rp

app = Flask(__name__)

@app.route('/')
def hello_world():
  return 'Hello from Flask!'
@app.route('/main', methods=['POST'])
def main():
	if request.method == 'POST':
		image_path = request.form['image_path']
		base64_image=base64.b64encode(rp.get(image_path).content)
		access_token = 'AIzaSyDMTvUK6Mlr_BWwwjJ3eFVxhGDKixlFgjQ'
		service = Service('vision', 'v1', access_token=access_token)
		body = {
			'requests': [{
			    'image': {
			    	'content': base64_image,
			    },
			'features': [{
				'type': 'TEXT_DETECTION',
				'maxResults': 1,
				}]
			}]
		}
		response = service.execute(body=body)
		res = response['responses'][0]['textAnnotations']
		json_data = json.dumps({'res':res[0]})
		return json_data
	return None
if __name__ == '__main__':
  app.run()