from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import random
import json
import logging

# opentelemetry
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# end opentelemetry

# dynatrace opentelemetry
merged = dict()
for name in ["dt_metadata_e617c525669e072eebe3d0f08212e8f2.json", "/var/lib/dynatrace/enrichment/dt_metadata.json"]:
    try:
        data = ''
        with open(name) as f:
          data = json.load(f if name.startswith("/var") else open(f.read()))
        merged.update(data)
    except:
        pass

merged.update({
    "service.name": "vote", #TODO Replace with the name of your application
    "service.version": "1.0", #TODO Replace with the version of your application
})
resource = Resource.create(merged)

tracer_provider = TracerProvider(sampler=sampling.ALWAYS_ON, resource=resource)
trace.set_tracer_provider(tracer_provider)

tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(
        endpoint="https://<tenant>/api/v2/otlp/v1/traces",
        headers={
          "Authorization": "Api-Token dt0c01.<TOKEN>" #TODO Replace <TOKEN> with your API Token as mentioned in the next step
        },
    )))
# end dynatrace opentelemetry

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)
# opentelemetry
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
RedisInstrumentor().instrument()
# end opentelemetry

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        # opentelemetry
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("processVote") as span1:
            app.logger.info('POST request tracer')
            span1.set_attribute("voter_id", voter_id)
            span1.set_attribute("vote", vote)
        # end opentelemetry
            app.logger.info('Received vote for %s', vote)
            data = json.dumps({'voter_id': voter_id, 'vote': vote})
            # opentelemetry
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("redisPush") as span2:
                app.logger.info('Redis push tracer')
                span2.set_attribute("voter_id", voter_id)
                span2.set_attribute("vote", vote)
                # end opentelemetry
                redis.rpush('votes', data)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
