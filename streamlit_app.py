# SECTION 1: Import Libraries and Load Data

import streamlit as st
import pandas as pd
import random
import re

st.set_page_config(
    page_title="SnowPro Core Study App",
    page_icon="❄️",
)

# Load questions from CSV
@st.cache_data
def load_data():
    file_path = 'all_questions - Sheet1.csv'  # Updated file path
    data = pd.read_csv(file_path)

    # Ensure QID column is treated as string
    data['QID'] = data['QID'].astype(str)

    return data

questions_df = load_data()

# SECTION 2: Utility Functions

# Shuffle answer options once per question
def shuffle_answers(row, question_key):
    if f"{question_key}_shuffled" not in st.session_state:
        options = [row[letter] for letter in ['A', 'B', 'C', 'D', 'E', 'F'] if pd.notna(row[letter])]
        random.shuffle(options)
        st.session_state[f"{question_key}_shuffled"] = options
    return st.session_state[f"{question_key}_shuffled"]

# Function to extract and display multiple documentation links using regex
def display_snowflake_docs(doc_string):
    # Check if the input is a valid string, otherwise return an empty list
    if isinstance(doc_string, str):
        # Regex pattern to detect URLs
        url_pattern = r'(https?://[^\s,]+)'
        
        # Find all URLs in the documentation string
        doc_links = re.findall(url_pattern, doc_string)
        
        # Display each link as Snowflake Documentation(1), Snowflake Documentation(2), etc.
        return [f"[Snowflake Documentation({i+1})]({link})" for i, link in enumerate(doc_links)]
    else:
        # If the value is not a string (e.g., NaN), return an empty list
        return []

# Callback function to move to the next question
def next_question():
    st.session_state['current_question'] += 1

# Callback function to exit and show the score
def exit_quiz():
    st.session_state['current_question'] = len(st.session_state['selected_questions'])

# Callback function to restart the quiz
def restart_quiz():
    st.session_state.clear()

# Callback function to start the quiz
def start_quiz_callback():
    st.session_state['quiz_started'] = True
    st.session_state['score'] = 0
    st.session_state['answered_questions'] = 0  # Track how many questions were answered
    st.session_state['current_question'] = 0

    # Shuffle and select questions for the quiz
    num_questions = st.session_state['num_questions']
    st.session_state['selected_questions'] = questions_df.sample(n=int(num_questions)).reset_index(drop=True)

# SECTION 3: Display Questions

# Function to display a single question
# Function to display a single question with optional image
def display_question(question_row, question_number, total_questions):
    st.write(f"### Question {question_number + 1} of {total_questions}")
    st.write(question_row['QUESTION'])

    # Check if there is an image for this question and display it
    if pd.notna(question_row.get('Image URL')):
        st.image(question_row['Image URL'], caption="Related Image", use_column_width=True)

        # Check if the image URL is correct for debugging purposes
        st.write(f"Image URL for this question: {question_row['Image URL']}")

    # Unique key for each question
    question_key = f"question_{question_number}"

    # Shuffle answers once per question
    options = shuffle_answers(question_row, question_key)

    # Determine if multiple answers are correct
    correct_answers = [question_row[letter.strip()] for letter in question_row['CORRECT ANSWER'].split(',')]
    num_correct = len(correct_answers)

    # Initialize session state for the question
    if question_key not in st.session_state:
        st.session_state[question_key] = {
            'submitted': False,
            'answered_correctly': False,
            'selected_options': None
        }

    # Display answer options only if the question hasn't been submitted yet
    if not st.session_state[question_key]['submitted']:
        if num_correct > 1:
            st.write(f"*(Select {num_correct} answers)*")
            selected_options = st.multiselect(
                "Your Answer:",
                options,
                key=f"{question_key}_selected"
            )
        else:
            selected_option = st.radio(
                "Your Answer:",
                options,
                key=f"{question_key}_selected",
                index=None  # No option pre-selected
            )
            selected_options = [selected_option] if selected_option else []

        # 'Submit' button
        if st.button("Submit", key=f"submit_{question_number}"):
            if len(selected_options) != num_correct:
                st.warning(f"Please select exactly {num_correct} option(s).")
            else:
                st.session_state[question_key]['submitted'] = True
                st.session_state['answered_questions'] += 1  # Increment the count of answered questions
                st.session_state[question_key]['selected_options'] = selected_options

                # Check if the answer is correct
                if set(selected_options) == set(correct_answers):
                    st.session_state['score'] += 1
                    st.session_state[question_key]['answered_correctly'] = True
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect! The correct answer(s): {', '.join(correct_answers)}")

                # Display explanation and documentation immediately after submitting
                if pd.notna(question_row['EXPLANATION/NOTES']):
                    st.info(f"**Explanation:** {question_row['EXPLANATION/NOTES']}")
                
                # Handle multiple Snowflake documentation links
                if pd.notna(question_row['Snowflake Documentation']):
                    doc_links = display_snowflake_docs(question_row['Snowflake Documentation'])
                    for link in doc_links:
                        st.write(link)

                # Add this question's data to review list
                if 'quiz_review' not in st.session_state:
                    st.session_state['quiz_review'] = []
                
                st.session_state['quiz_review'].append({
                    'Question': question_row['QUESTION'],
                    'Your Answer': ', '.join(selected_options),
                    'Correct Answer': ', '.join(correct_answers),
                    'Correct?': 'Yes' if set(selected_options) == set(correct_answers) else 'No',
                    'Explanation': question_row['EXPLANATION/NOTES'] if pd.notna(question_row['EXPLANATION/NOTES']) else 'N/A',
                    'Snowflake Documentation': ', '.join(display_snowflake_docs(question_row['Snowflake Documentation']))
                })

# SECTION 4: Display Navigation Buttons and Review Table

    else:
        # Display feedback if already submitted
        if st.session_state[question_key]['answered_correctly']:
            st.success("Correct!")
        else:
            st.error(f"Incorrect! The correct answer(s): {', '.join(correct_answers)}")

        # Display explanation and documentation
        if pd.notna(question_row['EXPLANATION/NOTES']):
            st.info(f"**Explanation:** {question_row['EXPLANATION/NOTES']}")

        if pd.notna(question_row['Snowflake Documentation']):
            doc_links = display_snowflake_docs(question_row['Snowflake Documentation'])
            for link in doc_links:
                st.write(link)

        # Add this question's data to review list (if not already added)
        if 'quiz_review' not in st.session_state:
            st.session_state['quiz_review'] = []
        
        if question_key not in [q['Question'] for q in st.session_state['quiz_review']]:
            st.session_state['quiz_review'].append({
                'Question': question_row['QUESTION'],
                'Your Answer': ', '.join(st.session_state[question_key]['selected_options']),
                'Correct Answer': ', '.join(correct_answers),
                'Correct?': 'Yes' if st.session_state[question_key]['answered_correctly'] else 'No',
                'Explanation': question_row['EXPLANATION/NOTES'] if pd.notna(question_row['EXPLANATION/NOTES']) else 'N/A',
                'Snowflake Documentation': ', '.join(display_snowflake_docs(question_row['Snowflake Documentation']))
            })

    # Show the 'Next' button after feedback and explanation
    if st.session_state[question_key]['submitted']:
        st.button("Next", key=f"next_{question_number}", on_click=next_question)

    # Navigation buttons
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.button("Exit and View Score", on_click=exit_quiz)
    with col2:
        st.button("Restart Quiz", on_click=restart_quiz)

# Function to display the review of the quiz at the end
def display_quiz_review():
    if 'quiz_review' in st.session_state and st.session_state['quiz_review']:
        st.write("## Quiz Review")
        
        # Create a DataFrame from the quiz review data
        review_df = pd.DataFrame(st.session_state['quiz_review'])

        # Reorder the columns (removing the 'Question Number' column)
        review_df = review_df[['Question', 'Correct?', 'Correct Answer', 'Your Answer', 'Explanation', 'Snowflake Documentation']]

        # Replace the 'Snowflake Documentation' column with the full URLs, removing the "Snowflake Documentation(1)" text
        review_df['Snowflake Documentation'] = review_df['Snowflake Documentation'].apply(lambda doc: ', '.join(re.findall(r'\((https?://[^\)]+)\)', doc)))

        # Shift the index to start at 1 instead of 0
        review_df.index += 1

        # Display the DataFrame with st.write() (this avoids the index column being displayed explicitly)
        st.write(review_df)

# SECTION 5: Main Quiz Logic and Final Output

# Function to start the quiz interface
def start_quiz():
    st.header("❄️ :blue[SnowPro Core] Study App",divider="grey")

    st.title("❄️ :blue[SnowPro Core] Study App - Test Mode")

    # --- TEST MODE: Add the QID input for testing specific questions ---
    qid = st.text_input(
        "Enter the QID to test a specific question (for debugging):"
    )

  # Image URL Test (Insert your direct image URL here)
    test_image_url = 'https://i.imgur.com/0u4Zjc4.jpeg'
    st.write("Testing Image URL:")
    st.image(test_image_url, caption="Test Image", use_column_width=True)

    # Button to test the specific question by QID
    if st.button("Test Question"):
        # Convert QID input to string to handle any type differences
        qid_str = str(qid)

        # Ensure QID column is treated as string for comparison
        questions_df['QID'] = questions_df['QID'].astype(str)

        # Search for the question in the DataFrame by QID
        matching_questions = questions_df[questions_df['QID'] == qid_str]

        # Check if a matching question was found
        if not matching_questions.empty:
            question_row = matching_questions.iloc[0]  # Get the first matching row
            display_question(question_row, question_number=0, total_questions=1)  # Display the question for testing
        else:
            st.error("Question not found! Please ensure you entered the correct QID.")

        return  # Exit after testing

    # --- REGULAR QUIZ LOGIC FOLLOWS BELOW ---

    # Initialize session state variables
    if 'quiz_started' not in st.session_state:
        st.session_state['quiz_started'] = False
    if 'score' not in st.session_state:
        st.session_state['score'] = 0
    if 'current_question' not in st.session_state:
        st.session_state['current_question'] = 0
    if 'answered_questions' not in st.session_state:
        st.session_state['answered_questions'] = 0

    # Display instructions and number of questions input before starting the quiz
    if not st.session_state['quiz_started']:
        # Display instructions
        st.markdown("""
            *Welcome to the SnowPro Core Study App! Review key concepts by building a quiz from a bank of over 400 practice questions. Check out the instructions below and :rainbow[happy studying!]*
            ### Instructions:
            1. Input the number of questions you want to be quizzed on (max 400).
            2. Make your answer selection then click :blue[**[Submit]**]. 
            3. After each question you will see if you answered correctly or not, as well as the explanation and link(s) to relevant Snowflake Documentation.
            4. Click :blue[**[Next]**] to move to the next question.
            5. Use :blue[**[Exit and View Score]**] to end the quiz at any time to see how you scored on *only the questions you submitted*.
            6. Once the quiz ends (either via :blue[**[Exit and View Score]**] or by completing all questions), click :blue[**[Review Quiz]**] to review all the questions and your responses in a table that you can even download to a .csv! (Use this to keep track of concepts and Snowflake Documentation that would be helpful to review)
            7. Use :blue[**[Restart Quiz]**] to **reset** the quiz. :blue-background[Note: You will not get a score or an ability to review the questions when using :blue[**[Restart Quiz]**].]
        """)
        st.markdown("""Lastly, mistakes happen, if you find a bug in the quiz or an inconsistency in a question/answer, please flag those and share feedback via the app's GitHub repository.""")

        # Input for selecting the number of questions
        st.session_state['num_questions'] = st.number_input(
            "Input number of questions:",
            min_value=1,
            max_value=len(questions_df),
            value=100,
            help="Maximum 400 questions"
        )

        # Start Quiz button
        st.button("Start Quiz", on_click=start_quiz_callback)

    else:
        total_questions = len(st.session_state['selected_questions'])
        current_q = st.session_state['current_question']

        if current_q < total_questions:
            question_row = st.session_state['selected_questions'].iloc[current_q]
            display_question(question_row, current_q, total_questions)
            st.progress((current_q + 1) / total_questions)
        else:
            answered_questions = st.session_state['answered_questions']
            total_selected_questions = st.session_state['num_questions']
            
            # Calculate percentage
            if answered_questions > 0:
                percentage = (st.session_state['score'] / answered_questions) * 100
            else:
                percentage = 0.0
            
            # Display results with percentage
            st.write(f"## Quiz Completed!")
            st.write(f"**Your Score:** {st.session_state['score']} out of {answered_questions} questions answered (Total exam: {total_selected_questions})")
            st.write(f"**Percentage:** {percentage:.2f}%")
            
            # Button to restart the quiz
            st.button("Restart Quiz", on_click=restart_quiz)
            
            # Button to review the quiz
            if st.button("Review Quiz"):
                display_quiz_review()

# Run the quiz app
if __name__ == '__main__':
    start_quiz()

