#import "@preview/touying:0.7.3": *
#import themes.simple: *

#show: simple-theme.with(aspect-ratio: "16-9")


/// A template for presentations based on your settings.
#let project(
  title: "",
  subtitle: none,
  authors: (),
  date: none,
  course: none,
  body,
) = {
  show: simple-theme.with(
    aspect-ratio: "16-9",
    config-info(
      title: title,
      subtitle: subtitle,
      author: authors.join(", "),
      date: date,
      institution: course,
    ),
  )

  // Your specific settings from presentation.typ
  set text(lang: "sv")
  set heading(numbering: none)
  set cite(style: "american-institute-of-physics")
  set math.equation(numbering: "(1)")

  // Custom styling to match your preferences if needed
  // (e.g., page numbering is handled by the theme)

  body
}
