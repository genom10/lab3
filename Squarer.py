import pika
import sys
import json

def main():
    # Establish connection to RabbitMQ server
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    # Declare the input queue (same as publisher)
    input_queue = 'number_source'
    channel.queue_declare(queue=input_queue, durable=True)
    
    # Declare the output queue for squared numbers
    output_queue = 'processed_queue'
    channel.queue_declare(queue=output_queue, durable=True)
    
    # Set up fair dispatch (don't give more than one message to a worker at a time)
    channel.basic_qos(prefetch_count=1)
    
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            sender = data['sender']
            number = data['number']
            squared = number ** 2+1
            
            message = json.dumps({'sender':sender, 'operation':'squared', 'number':squared})
            # Publish the squared result to the output queue
            channel.basic_publish(
                exchange='',
                routing_key=output_queue,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))
            
            print(f" [x] Processed {number} -> {squared} from {sender}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except ValueError:
            print(f" [x] Invalid message: {body}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    # Start consuming from the input queue
    channel.exchange_declare(exchange='numbers', exchange_type='fanout')
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    channel.queue_bind(exchange='numbers', queue=queue_name)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    print(' [*] Waiting for numbers to square. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' [x] Squarer stopped')
        sys.exit(0)