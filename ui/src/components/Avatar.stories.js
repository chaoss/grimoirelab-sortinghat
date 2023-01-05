import Avatar from "./Avatar.vue";

export default {
  title: "Avatar",
  excludeStories: /.*Data$/
};

const avatarTemplate = '<avatar :name="name" :email="email" />';

export const Default = () => ({
  components: { Avatar },
  template: avatarTemplate,
  props: {
    name: {
      default: "Tom Marvolo Riddle"
    },
    email: {
      default: null
    }
  }
});

export const SingleInitial = () => ({
  components: { Avatar },
  template: avatarTemplate,
  props: {
    name: {
      default: "Voldemort"
    },
    email: {
      default: null
    }
  }
});

export const Gravatar = () => ({
  components: { Avatar },
  template: avatarTemplate,
  props: {
    name: {
      default: "Santiago Dueñas"
    },
    email: {
      default: "sduenas@bitergia.com"
    }
  }
});
