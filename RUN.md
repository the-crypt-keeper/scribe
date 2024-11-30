SAMPLES=10

# openai (chat)
python3 ./world_builder.py Meta-Llama-3.1-405B-Instruct --num_samples $SAMPLES &

# tabbyapi (chat)
python3 ./world_builder.py gemma-2-9b-it-exl2-6.0bpw --num_samples $SAMPLES --num_batch 2 &

# tabbyapi (completion)
python3 ./world_builder.py Fimbulvetr-11B-v2-6.0bpw-h6-exl2 --tokenizer internal:alpaca --num_samples $SAMPLES --num_batch 2 &

# llama-server (completion)
python3 ./world_builder.py Dusk_Rainbow_Ep03-Q6_K --tokenizer SicariusSicariiStuff/Dusk_Rainbow --num_samples $SAMPLES &

# llama-server (chat)
python3 ./world_builder.py L3.1-8B-Celeste-V1.5.Q6_K --num_samples $SAMPLES &

wait