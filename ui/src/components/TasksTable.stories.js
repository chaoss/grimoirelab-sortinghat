import TasksTable from "./TasksTable.vue";

export default {
  title: "TasksTable",
  excludeStories: /.*Data$/,
};

const template = `
  <tasks-table
    :fetch-backends="fetchBackends"
    :fetch-tasks="fetchTasks"
    :create-task="() => {}"
    :delete-task="deleteTask"
    :edit-task="() => {}"
  />
`;

export const Default = () => ({
  components: { TasksTable },
  template: template,
  data: () => ({
    backends: {
      data: {
        identitiesImportersTypes: [
          { name: "mailmap", args: ["url"] },
          { name: "external plugin", args: ["url", "token"] },
        ],
      },
    },
    tasks: {
      data: {
        importIdentitiesTask: {
          entities: [
            {
              id: 1,
              backend: "mailmap",
              url: "http://test.com",
              interval: 43800,
              lastExecution: "2023-03-14T14:21:10.041445+00:00",
              failed: true,
              scheduledDatetime: "2023-03-14T14:56:10.041450+00:00",
              failures: 1,
              executions: 22,
            },
            {
              id: 2,
              backend: "external plugin",
              url: "http://test.com",
              args: JSON.stringify({ token: "XXXX" }),
              interval: 0,
              lastExecution: "2023-03-12T11:01:40.041445+00:00",
              failed: false,
              failures: 0,
              executions: 1,
            },
          ],
        },
      },
    },
  }),
  methods: {
    fetchBackends() {
      return this.backends;
    },
    fetchTasks() {
      return this.tasks;
    },
    deleteTask(id) {
      this.tasks.data.importIdentitiesTask.entities =
        this.tasks.data.importIdentitiesTask.entities.filter(
          (task) => task.id !== id
        );
      return {
        data: {
          deleteImportIdentitiesTask: {
            deleted: true,
          },
        },
      };
    },
  },
});

export const Empty = () => ({
  components: { TasksTable },
  template: template,
  data: () => ({
    backends: {
      data: {
        identitiesImportersTypes: [
          { name: "mailmap", args: ["url"] },
          { name: "external plugin", args: ["url", "token"] },
        ],
      },
    },
    tasks: {
      data: {
        importIdentitiesTask: {
          entities: [],
        },
      },
    },
  }),
  methods: {
    fetchBackends() {
      return this.backends;
    },
    fetchTasks() {
      return this.tasks;
    },
    deleteTask() {
      return;
    },
  },
});
