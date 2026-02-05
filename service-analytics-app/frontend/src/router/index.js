import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import SurveyView from '../views/SurveyView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/survey/:surveyId',
    name: 'SurveyView',
    component: SurveyView,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

