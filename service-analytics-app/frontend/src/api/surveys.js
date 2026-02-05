import axios from 'axios'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const surveysApi = {
  getSurveys: () => api.get('/surveys/'),
  getSurveyQuestions: (surveyId) => api.get(`/surveys/${surveyId}/questions`),
  validateQuestions: (surveyId, questionIds) => 
    api.post('/surveys/validate-questions', {
      survey_id: surveyId,
      question_ids: questionIds
    }),
  getResponses: (surveyId, questionIds) =>
    api.post('/surveys/responses', {
      survey_id: surveyId,
      question_ids: questionIds
    }),
  getAllResponses: (surveyId) =>
    api.get(`/surveys/${surveyId}/all-responses`),
  getAnswerOptions: (questionIds) =>
    api.get(`/answer-options/questions/${questionIds.join(',')}`)
}

