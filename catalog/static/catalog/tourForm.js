document.addEventListener("DOMContentLoaded", () => {
  const addButton = document.getElementById("addItinerary");
  const rows = document.getElementById("itineraryRows");
  const totalForms = document.getElementById("id_itineraries-TOTAL_FORMS");
  const emptyForm = document.getElementById("emptyItinerary");
  if (!addButton || !rows || !totalForms || !emptyForm) return;

  addButton.addEventListener("click", () => {
    const index = Number(totalForms.value);
    const fragment = emptyForm.content.cloneNode(true);
    fragment.querySelectorAll("[name], [id], [for]").forEach((element) => {
      ["name", "id", "for"].forEach((attribute) => {
        if (element.hasAttribute(attribute)) {
          element.setAttribute(attribute, element.getAttribute(attribute).replaceAll("__prefix__", String(index)));
        }
      });
    });
    rows.appendChild(fragment);
    totalForms.value = String(index + 1);
    rows.lastElementChild.querySelector("input:not([type='hidden'])")?.focus();
  });
});
