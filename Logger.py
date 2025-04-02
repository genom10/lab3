import pika
from datetime import datetime
import json

LOG_FILE = 'rabbitmq_messages.log'

def setup_logging():
    with open(LOG_FILE, 'w') as f:
        f.write(f"\n\n=== Log started at {datetime.now().isoformat()} ===\n")

def log_message(body):
    timestamp = datetime.now().isoformat()
    msg = json.loads(body)
    try:
        message_type = msg['operation']
    except KeyError:
        message_type = "original"

    try:
        log_entry = f"[{timestamp}] {msg['sender']} : {message_type} : {msg['number']}\n"
    except:
        log_entry = f"UNKNOWN MESSAGE {body}"

    with open(LOG_FILE, 'a') as f:
        f.write(log_entry)
    print(log_entry.strip())

def number_callback(ch, method, properties, body):
    log_message(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main(): 
    #TO WRITE start *************************************************************************
    setup_logging()
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    # Set up fanout exchange for original numbers
    channel.exchange_declare(exchange='numbers', exchange_type='fanout')
    num_result = channel.queue_declare(queue='', exclusive=True)
    num_queue = num_result.method.queue
    channel.queue_bind(exchange='numbers', queue=num_queue)
    
    # Regular queue for squared numbers
    channel.queue_declare(queue='processed_queue', durable=True)
    
    channel.basic_consume(queue=num_queue, on_message_callback=number_callback)
    channel.basic_consume(queue='processed_queue', on_message_callback=number_callback)
    
    print(' [*] Logger started. Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()
    #TO WRITE finish *************************************************************************

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' [*] Logger stopped')