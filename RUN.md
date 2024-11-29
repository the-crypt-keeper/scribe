# openai
python3 ./world_builder.py Meta-Llama-3.1-405B-Instruct --num_samples 1

# tabbyapi (chat template)
python3 ./world_builder.py gemma-2-9b-it-exl2-6.0bpw --num_samples 1 --num_batch 2

# tabbyapi (no chat template)
python3 ./world_builder.py Fimbulvetr-11B-v2-6.0bpw-h6-exl2 --tokenizer internal:alpaca --num_samples 1 --num_batch 2

# llama-server
python3 ./world_builder.py llama/Dusk_Rainbow_Ep03-Q6_K --tokenizer SicariusSicariiStuff/Dusk_Rainbow --num_samples 1