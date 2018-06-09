import threading

user_data_dir='/home/gitdog/data'

task_id_counter=1
task_id_counter_lock=threading.Lock()

Pendinng_queue=[]
Running_queue=[]
Failed_queue=[]
Success_queue=[]
Unkown_queue=[]

status_dict={}

task_queue_lock=threading.Lock()