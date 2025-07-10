"use client"

import React, { useMemo, useState } from "react"
import * as HeroIcons from "@heroicons/react/24/outline"

type Icons = {
  name: string
  friendly_name: string
  Component: React.FC<React.ComponentPropsWithoutRef<"svg">>
}

export const useIconPicker = (): {
  search: string
  setSearch: React.Dispatch<React.SetStateAction<string>>
  icons: Icons[]
} => {
  const icons: Icons[] = useMemo(
    () =>
      Object.entries(HeroIcons).map(([iconName, IconComponent]) => ({
        name: iconName,
        friendly_name: iconName.match(/[A-Z][a-z]+/g)?.join(" ") ?? iconName,
        Component: IconComponent,
      })),
    [],
  )

  const [search, setSearch] = useState("")
  
  const filteredIcons = useMemo(() => {
    return icons.filter((icon) => {
      if (search === "") {
        return true
      } else if (icon.name.toLowerCase().includes(search.toLowerCase())) {
        return true
      } else {
        return false
      }
    })
  }, [icons, search])

  return { search, setSearch, icons: filteredIcons }
}

export const IconRenderer = ({
  icon,
  ...rest
}: {
  icon: string
} & React.ComponentPropsWithoutRef<"svg">) => {
  const IconComponent = HeroIcons[icon as keyof typeof HeroIcons]

  if (!IconComponent) {
    return null
  }

  return <IconComponent data-slot="icon" {...rest} />
}