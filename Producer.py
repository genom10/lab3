import pika
import sys
import time
import json

def publish(publisher_name:str, max_number: int, delay: float):
    
    # Establish connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    # Declare a queue (will create if doesn't exist)
    # queue_name = 'number_source'
    # channel.queue_declare(queue=queue_name, durable=True)
    
    # Publish numbers from 0 to max_number with delay
    for number in range(0, max_number + 1):
        message = json.dumps({'sender':publisher_name, 'number':number})
        channel.exchange_declare(exchange='numbers', exchange_type='fanout')
        channel.basic_publish(
            exchange='numbers',
            routing_key='',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        print(f" Sent {message}")
        time.sleep(delay)
    
    connection.close()

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python publisher.py <publisher_name> <max_number> <delay_seconds>")
        sys.exit(1)
    
    try:
        publisher_name = str(sys.argv[1])
        max_number = int(sys.argv[2])
        delay = float(sys.argv[3])
    except ValueError:
        print("Error: <max_number> and <delay_seconds> arguments must be numbers")
        sys.exit(1)

    try:
        publish(publisher_name, max_number, delay)
    except KeyboardInterrupt:
        print('[x] Publisher stopped')
        sys.exit(0)