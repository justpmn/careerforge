
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 2 * 60 * 1000,
      gcTime: 30 * 60 * 1000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const queryKeys = {
  careers: ['careers'] as const,

  user: (userId: string) =>
    ['user', userId] as const,

  selectedCareer: (userId: string) =>
    ['user', userId, 'selected-career'] as const,

  roadmap: (userId: string, careerKey: string) =>
    ['user', userId, 'roadmap', careerKey] as const,

  recordedSkills: (userId: string) =>
    ['user', userId, 'recorded-skills'] as const,

  learningProgress: (userId: string, careerKey: string) =>
    ['user', userId, 'learning-progress', careerKey] as const,
    savedCv: (userId: string) =>
    ['user', userId, 'saved-cv'] as const,

  cvRecommendations: (userId: string) =>
    ['user', userId, 'cv-recommendations'] as const,

  coreCoverage: (userId: string) =>
    ['user', userId, 'core-coverage'] as const,

  roadmaps: (userId: string) =>
    ['user', userId, 'roadmap'] as const,

  competencyAssessments: (userId: string, careerKey: string) =>
    ['user', userId, 'competency-assessments', careerKey] as const,

  admin: (userId: string) =>
    ['admin', userId] as const,

  adminOverview: (userId: string) =>
    ['admin', userId, 'overview'] as const,

  adminUsers: (userId: string, page: number) =>
    ['admin', userId, 'users', page] as const,

  adminLogs: (
    userId: string,
    page: number,
    severity: string,
    category: string
  ) => ['admin', userId, 'logs', page, severity, category] as const,

  adminHealth: (userId: string) =>
    ['admin', userId, 'health'] as const,

  adminCareer: (userId: string, careerKey: string) =>
    ['admin', userId, 'career', careerKey] as const,

  adminResources: (userId: string) =>
    ['admin', userId, 'resources'] as const,

  adminResourceList: (
    userId: string,
    search: string,
    page: number,
    archived: boolean
  ) => ['admin', userId, 'resources', 'list', search, page, archived] as const,

  adminResourceOptions: (userId: string) =>
    ['admin', userId, 'resources', 'options'] as const,
  adminResourceSkills: (userId: string, search: string) =>
  ['admin', userId, 'resources', 'skills', search] as const,

};
