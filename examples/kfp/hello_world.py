# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "kfp==2.2.0",
# ]
# ///

from kfp import dsl
from kfp import compiler

@dsl.component
def say_hello(name: str) -> str:
    message = f'Hello, {name}!'
    print(message)
    return message

@dsl.pipeline(
    name='hello-world-pipeline',
    description='A simple intro pipeline.'
)
def hello_world_pipeline(recipient: str = 'World'):
    # Create the component task
    hello_task = say_hello(name=recipient)
    
    # Optional: Use the output in another way or just finish
    # print_task = print_op(msg=hello_task.output)

if __name__ == '__main__':
    # Compile the pipeline to a YAML file
    compiler.Compiler().compile(
        pipeline_func=hello_world_pipeline,
        package_path='hello_world_pipeline.yaml'
    )
    print("Pipeline compiled to hello_world_pipeline.yaml")
