import time
import json
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
        self.steps = {}
        
    def add_step(self, step):
        assert step.step not in self.steps
        step.setup(self)
        seq = len(list(self.steps.keys()))
        self.steps[step.step] = {
            'fn': step,
            'seq': seq,
            'queue': None
        }

    def save(self, key, id, payload):
        pass
    
    def load(self, key, id):
        pass
    
    def find(self, key):
        pass

    def all(self):
        pass
        
    def _execute_single_step(self, step_name, id, input):
        st = self.steps[step_name]['fn']
        print(f"> {step_name} executing {id}")
        try:
            output, meta = st.run(id, input)
        except Exception as e:
            print("ERROR: ", str(e))
        if output is not None:
            self.save(st.outkey, id, output)
            self.save('_'+st.outkey, id, meta)
            
    def _create_work_thread(self, step_name):
        st = self.steps[step_name]['fn']       
        num_parallel = int(st.params.get('num_parallel', '1'))
        self.steps[step_name]['queue'] = ThreadPoolExecutor(max_workers=num_parallel)
        self.steps[step_name]['futures'] = []
    
    def _queue_work(self, step_name, id, input):
        if self.steps[step_name]['queue'] is None:
            self._create_work_thread(step_name)
        future = self.steps[step_name]['queue'].submit(self._execute_single_step, step_name, id, input)
        self.steps[step_name]['futures'].append(future)
        return future
    
    def _unfinished_futures(self, step_name):
        if self.steps[step_name]['queue'] is None:
            return []
        return [future for future in self.steps[step_name]['futures'] if not future.done()]

    def _join_work_thread(self, step_name):
        if self.steps[step_name]['queue'] is not None:
            # Wait for all futures to complete
            for future in self.steps[step_name]['futures']:
                future.result()
            self.steps[step_name]['queue'].shutdown(wait=True)
            self.steps[step_name]['queue'] = None
            self.steps[step_name]['futures'] = []
    
    def shutdown(self):
        for step_name in self.steps:
            self._join_work_thread(step_name)
            
    def run_all_steps(self, sleep_delay = 5):
        while True:
            new_work = False
            for step_name, step_info in sorted(self.steps.items(), key=lambda x: x[1]['seq']):
                step = step_info['fn']
                if not step.enabled: continue
                pending_inputs = list(step.pending_inputs())
                if pending_inputs:
                    for id, input in pending_inputs:
                        self._queue_work(step_name, id, input)
                    new_work = True
                    
            if new_work:
                time.sleep(sleep_delay)
                continue
            
            for step_name in self.steps:
                if self._unfinished_futures(step_name):
                    print(f'{step_name} busy, waiting...')
                    time.sleep(sleep_delay)
                    continue

            # If there was no new work and there are no pending futures, the process is complete
            for step_name in self.steps:
                self._join_work_thread(step_name)
                
            break  # Exit the while loop

class SQLiteScribe(Scribe):
    def __init__(self, project):
        super().__init__(project)
        
        self.dbname = f'{project}.db'
        
        self.db = sqlite3.connect(self.dbname)
        self.db.execute('''CREATE TABLE IF NOT EXISTS data
                           (key TEXT, id TEXT, payload TEXT,
                            PRIMARY KEY (key, id))''')
        self.db.commit()
           
    def save(self, key, id, payload):
        with sqlite3.connect(self.dbname) as db:
            db.execute('INSERT OR REPLACE INTO data (key, id, payload) VALUES (?, ?, ?)', (key, id, json.dumps(payload)))
    
    def load(self, key, id):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT payload FROM data WHERE key = ? AND id = ?', (key, id))
            result = cursor.fetchone()
        return json.loads(result[0]) if result else None
    
    def find(self, key):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT id, payload FROM data WHERE key = ?', (key,))
        return [(row[0], json.loads(row[1])) for row in cursor.fetchall()]

    def all(self):
        with sqlite3.connect(self.dbname) as db:
            cursor = db.execute('SELECT id, payload, key FROM data')
        return [(row[2], row[0], json.loads(row[1])) for row in cursor.fetchall()]
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scribe CLI")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    args = parser.parse_args()
    
    sc = SQLiteScribe(project=args.project)
    docs = sc.all()
    for key, id, content in docs:
        print(id, key, type(content), str(content)[0:40])
