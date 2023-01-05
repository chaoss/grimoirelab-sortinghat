import ProfileCard from "./ProfileCard.vue";

export default {
  title: "ProfileCard",
  excludeStories: /.*Data$/
};

const profileCardTemplate =
  '<profile-card :name="name" :identities="identities" :enrollments="enrollments" />';

export const Default = () => ({
  components: { ProfileCard },
  template: profileCardTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    identities: {
      default: () => [
        {
          name: "GitHub",
          identities: [
            {
              uuid: "006afa",
              name: "Tom Marvolo Riddle",
              email: "triddle@example.net",
              username: "triddle"
            },
            {
              uuid: "808b18",
              name: "Voldemort",
              email: "-",
              username: "voldemort"
            }
          ]
        },
        {
          name: "Git",
          identities: [
            {
              uuid: "abce32",
              name: "voldemort",
              email: "voldemort@example.net",
              username: "voldemort"
            }
          ]
        },
        {
          name: "Others",
          identities: [
            {
              uuid: "4ce562",
              name: "-",
              email: "-",
              username: "voldemort",
              source: "irc"
            }
          ]
        }
      ]
    },
    enrollments: {
      default: () => [
        {
          organization: {
            name: "Hogwarts School of Witchcraft and Wizardry",
            id: "1"
          },
          start: "1938-09-01",
          end: "1945-06-02T00:00:00+00:00"
        },
        {
          organization: {
            name: "Slytherin House",
            id: "2"
          },
          start: "1938-09-01T00:00:00+00:00",
          end: "1998-05-02T00:00:00+00:00"
        }
      ]
    }
  }
});
