
const colors = ["orange", "brown", " green", "blue", "red", "black", "magenta", "yellow"]

async function post(userId, chipId, dropletId, featureId, value){
  rep = await fetch("/droplet/feature/save", {
      method: "POST",
      body: JSON.stringify({
          user_id: userId,
          chip_id: chipId,
          droplet_id: dropletId,
          feature_id: featureId,
          value: value
      }),
      headers: {
          "Content-type": "application/json; charset=UTF-8"
      }
  });
  return {rep};
};

async function remove(chip_id, droplet_id){
  rep = await fetch("/droplet/feature/remove", {
      method: "POST",
      body: JSON.stringify({
        chip_id: chip_id,
        droplet_id: droplet_id
      }),
      headers: {
          "Content-type": "application/json; charset=UTF-8"
      }
  });
  return {rep};
}
