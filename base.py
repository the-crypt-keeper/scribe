import time
import json
import copy
from concurrent.futures import ThreadPoolExecutor
import sqlite3

SAMPLER = {
    'temperature': 1.0,
    'min_p': 0.05,
    'repetition_penalty': 1.1,
    'max_tokens': 3072,
    'min_tokens': 10 
}

class Scribe():
    def __init__(self, project):
        self.project = project       
        self.steps = []
        
    def add_step(self, step):
        assert step.step not in self.steps
        step.setup(self)
        self.steps.append(step)
        self._create_work_thread(step)

    def db_start(self, key, id):
        pass

    def db_end(self, key, id, payload, meta):
        pass

    def db_abort(self, key, id):
        pass

    def load(self, key, id):
        pass

    def find(self, key=None, id=None):
        pass

    def all_keys(self):
        pass

    def all_ids(self):
        pass
        
    def _execute_single_step(self, st, id, input):
        step_name = st.step
        print(f"> {step_name} executing {id}")
        if not self.db_start(st.outkey, id):
            print(f"ERROR: {step_name} for {id} already exists")
            return
        try:
            output, meta = st.run(id, input)
            if output is not None:
                self.db_end(st.outkey, id, output, meta)
            else:
                print(f"ERROR: {step_name} for {id} returned nothing.")
                self.db_abort(st.outkey, id)
        except Exception as e:
            print(f"ERROR: _execute_single_step {step_name} crashed: {str(e)}")
            self.db_abort(st.outkey, id)
            
    def _create_work_thread(self, st):
        num_parallel = int(st.params.get('parallel', '1'))            
        st.queue = ThreadPoolExecutor(max_workers=num_parallel)
    
    def _queue_work(self, st, id, input):
        assert st.queue != None
        future = st.queue.submit(self._execute_single_step, st, id, input)
        st.futures[id] = future
        return future
    
    def _unfinished_futures(self, st):
        if st.queue is None: return []
        return [future for id, future in st.futures.items() if not future.done()]

    def _join_work_thread(self, st):
        if st.queue is None: return
        for future in st.futures.values(): future.result()
        st.queue.shutdown(wait=True)
        st.queue = None
        st.futures = {}
    
    def shutdown(self):
        for st in self.steps:
            self._join_work_thread(st)

    def run_all_steps(self, small_delay = 1, big_delay = 5):
        while True:
            did_work = False
            next_steps = []
            
            for step in self.steps:
                print(f"--> {step.step}")
                if step.queue_full(): 
                    print(f'{step.step} queue is full')
                    next_steps.insert(0, step)
                    continue
                
                try:
                    pending_inputs = list(step.pending_inputs())
                except Exception as e:
                    print(f"ERROR: pending_inputs failed on {step.step}: {str(e)}")
                    pending_inputs = []
                   
                if len(pending_inputs) > 0:
                    id, input = pending_inputs[0]
                    print(f'{step.step} queued job {id}, still pending {len(pending_inputs)-1}.')
                    try:
                        self._queue_work(step, id, input)
                    except Exception as e:
                        print(f"ERROR: _queue_work failed on {step.step}: {str(e)}")
                    did_work = True
                    next_steps.append(step)
                else:
                    next_steps.insert(0, step)

            self.steps = next_steps
                    
            if did_work:
                time.sleep(small_delay)
                continue
            else:            
                for st in self.steps:
                    num_unfinished = len(st.unfinished_futures())
                    if num_unfinished > 0:
                        print(f'{st.step} busy, queue depth {num_unfinished}...')
                        did_work = True
            
            if did_work:        
                time.sleep(big_delay)
                continue

            # If there was no new work and there are no pending futures, the process is complete
            print('Nothing left to do, shutting down.')
            self.shutdown()
            break

    def init_pipeline(self, args, PIPELINE):
        STEPS = {x.step: x for x in PIPELINE}
        print("Available Steps:", ', '.join(list(STEPS.keys())))
        
        for step_group in args:
            for step_arg in step_group:
                escaped_step_arg = step_arg.replace('//','%%')
                step_name, *parts = escaped_step_arg.split('/')
                parts = [p.replace('%%','/') for p in parts]
                
                if step_name not in STEPS:
                    raise Exception(f'Step {step_name} was not found, should be one of: {", ".join(STEPS.keys())}')
                  
                new_step = copy.deepcopy(STEPS[step_name])                
                print(f"CONFIG STEP: {step_name}")
                for arg in parts:
                    k, v = arg.split('=')
                    print(f"-- ARG: {step_name}.{k} = {v}")
                    new_step.params[k] = v
                    
                self.add_step(new_step)
                
class SQLiteScribe(Scribe):
    def __init__(self, project):
        super().__init__(project)
        
        self.dbname = f'{project}.db'
        
        self.db = sqlite3.connect(self.dbname)
        self.db.execute('''CREATE TABLE IF NOT EXISTS data
                           (key TEXT, id TEXT, payload TEXT, meta TEXT,
                            PRIMARY KEY (key, id))''')
        self.db.commit()
           
    def db_start(self, key, id):
        try:
            with sqlite3.connect(self.dbname) as db:
                db.execute('INSERT INTO data (key, id, payload, meta) VALUES (?, ?, ?, ?)', (key, id, 'null', 'null'))
            return True
        except sqlite3.IntegrityError:
            return False

    def db_end(self, key, id, payload, meta):
        with sqlite3.connect(self.dbname) as db:
            db.execute('UPDATE data SET payload = ?, meta = ? WHERE key = ? AND id = ?', 
                       (json.dumps(payload), json.dumps(meta), key, id))

    def db_abort(self, key, id):
        with sqlite3.connect(self.dbname) as db:
            db.execute('DELETE FROM data WHERE key = ? AND id = ?', (key, id))

    def load(self, key, id):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT payload, meta FROM data WHERE key = ? AND id = ?', (key, id))
            result = cursor.fetchone()
        return (json.loads(result[0]), json.loads(result[1])) if result else (None, None)

    def find(self, key=None, id=None):
        with sqlite3.connect(self.dbname) as db:
            if key and id:
                cursor = db.execute('SELECT key, id, payload, meta FROM data WHERE key = ? AND id = ?', (key, id))
            elif key:
                cursor = db.execute('SELECT key, id, payload, meta FROM data WHERE key = ?', (key,))
            elif id:
                cursor = db.execute('SELECT key, id, payload, meta FROM data WHERE id = ?', (id,))
            else:
                cursor = db.execute('SELECT key, id, payload, meta FROM data')
        return [(row[0], row[1], json.loads(row[2]), json.loads(row[3])) for row in cursor.fetchall()]

    def all_keys(self):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT DISTINCT key FROM data')
        return [row[0] for row in cursor.fetchall()]

    def all_ids(self):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT DISTINCT id FROM data')
        return [row[0] for row in cursor.fetchall()]
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scribe CLI")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    args = parser.parse_args()
    
    sc = SQLiteScribe(project=args.project)
    
    print("All keys:")
    print(sc.all_keys())
    
    print("\nAll ids:")
    print(sc.all_ids())
    
    print("\nAll documents:")
    docs = sc.find()
    for key, id, payload, meta in docs:
        print(id, key, type(payload), str(payload)[0:40])
