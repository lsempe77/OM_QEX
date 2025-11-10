import pandas as pd

# Load comparison results
df = pd.read_csv('outputs/comparison/detailed_comparison.csv')

print('=' * 80)
print('GRADUATION COMPONENTS DETAILED COMPARISON')
print('=' * 80)

components = ['consumption_support', 'healthcare', 'assets', 'skills_training', 'savings', 'coaching', 'social_empowerment']

for comp in components:
    print(f'\n{comp.upper().replace("_", " ")}:')
    print(f'  LLM values: {df[comp + "_llm"].tolist()}')
    print(f'  Human values: {df[comp + "_human"].tolist()}')
    print(f'  Matches: {df[comp + "_match"].tolist()}')
    print(f'  Reasons: {df[comp + "_reason"].tolist()}')

print('\n' + '=' * 80)
print('OTHER KEY FIELDS')
print('=' * 80)

for field in ['author_name', 'country', 'program_name']:
    print(f'\n{field.upper().replace("_", " ")}:')
    print(f'  LLM: {df[field + "_llm"].tolist()}')
    print(f'  Human: {df[field + "_human"].tolist()}')
    print(f'  Match: {df[field + "_match"].tolist()}')
    print(f'  Reason: {df[field + "_reason"].tolist()}')
