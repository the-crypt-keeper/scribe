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
        
    def _execute_single_step(self, step_name, id, input):
        st = self.steps[step_name]['fn']
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
            
    def _create_work_thread(self, step_name):
        st = self.steps[step_name]['fn']       
        num_parallel = int(st.params.get('num_parallel', '1'))
        self.steps[step_name]['queue'] = ThreadPoolExecutor(max_workers=num_parallel)
        self.steps[step_name]['futures'] = {}
    
    def _queue_work(self, step_name, id, input):
        if self.steps[step_name]['queue'] is None:
            self._create_work_thread(step_name)
        future = self.steps[step_name]['queue'].submit(self._execute_single_step, step_name, id, input)
        self.steps[step_name]['futures'][id] = future
        return future
    
    def _unfinished_futures(self, step_name):
        if self.steps[step_name]['queue'] is None:
            return []
        return [future for id, future in self.steps[step_name]['futures'].items() if not future.done()]

    def _join_work_thread(self, step_name):
        if self.steps[step_name]['queue'] is not None:
            # Wait for all futures to complete
            for future in self.steps[step_name]['futures'].values():
                future.result()
            self.steps[step_name]['queue'].shutdown(wait=True)
            self.steps[step_name]['queue'] = None
            self.steps[step_name]['futures'] = {}
    
    def shutdown(self):
        for step_name in self.steps:
            self._join_work_thread(step_name)
            
    def run_all_steps(self, small_delay = 1, big_delay = 5):
        while True:
            did_work = False
            for step_name, step_info in self.steps.items():
                step = step_info['fn']
                if not step.enabled: continue
                try:
                    pending_inputs = list(step.pending_inputs())
                except Exception as e:
                    print(f"ERROR: pending_inputs failed on {step_name}: {str(e)}")
                # print(step_name, pending_inputs)
                if pending_inputs:
                    for id, input in pending_inputs:
                        print(f'{step_name} queued job {id}')
                        self._queue_work(step_name, id, input)
                    did_work = True
                    
            if did_work:
                time.sleep(small_delay)
                continue
            else:            
                for step_name in self.steps:
                    if self._unfinished_futures(step_name):
                        print(f'{step_name} busy, waiting...')
                        did_work = True
            
            if did_work:        
                time.sleep(big_delay)
                continue

            # If there was no new work and there are no pending futures, the process is complete
            print('Nothing left to do, shutting down.')
            for step_name in self.steps:                
                self._join_work_thread(step_name)                
            break

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
    
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scribe CLI")
    parser.add_argument("--project", type=str, required=True, help="Project name")
    args = parser.parse_args()
    
    sc = SQLiteScribe(project=args.project)
    docs = sc.find()
    for key, id, payload, meta in docs:
        print(id, key, type(payload), str(payload)[0:40])
